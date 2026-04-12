import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from blood_requests_app.models import BloodRequest, RequestResponse, ChatMessage
from donors.models import DonorAvailability


class LiveRequestsConsumer(AsyncWebsocketConsumer):
    """Broadcast new blood requests to all connected donors"""
    
    async def connect(self):
        self.room_group_name = 'live_requests'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        pass
    
    async def send_request_update(self, event):
        """Send new request to all donors"""
        await self.send(text_data=json.dumps({
            'type': 'new_request',
            'data': event['data']
        }))


class RequestTrackingConsumer(AsyncWebsocketConsumer):
    """Track specific request - donor locations and status updates"""
    
    async def connect(self):
        self.request_id = self.scope['url_route']['kwargs']['request_id']
        self.room_group_name = f'request_{self.request_id}'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        
        # Send current state
        await self.send_current_state()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        
        # Handle donor location update
        if data.get('type') == 'location_update':
            await self.update_donor_location(data)
    
    async def send_tracking_update(self, event):
        """Send tracking updates to requester"""
        await self.send(text_data=json.dumps(event['data']))
    
    @database_sync_to_async
    def send_current_state(self):
        """Send initial request state"""
        from .serializers import BloodRequestSerializer
        try:
            request = BloodRequest.objects.get(id=self.request_id)
            serializer = BloodRequestSerializer(request)
            self.send(text_data=json.dumps({
                'type': 'initial_state',
                'data': serializer.data
            }))
        except BloodRequest.DoesNotExist:
            pass
    
    @database_sync_to_async
    def update_donor_location(self, data):
        """Update donor location in database"""
        from accounts.models import User
        try:
            donor = User.objects.get(id=data['donor_id'])
            availability, _ = DonorAvailability.objects.get_or_create(donor=donor)
            availability.current_latitude = data['latitude']
            availability.current_longitude = data['longitude']
            availability.save()
            
            # Broadcast to requester
            self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'send.tracking.update',
                    'data': {
                        'type': 'donor_location',
                        'donor_id': data['donor_id'],
                        'latitude': data['latitude'],
                        'longitude': data['longitude']
                    }
                }
            )
        except Exception as e:
            print(f"Error updating location: {e}")


class ChatConsumer(AsyncWebsocketConsumer):
    """Real-time chat between donor and requester"""
    
    async def connect(self):
        self.request_id = self.scope['url_route']['kwargs']['request_id']
        self.user = self.scope['user']
        self.room_group_name = f'chat_{self.request_id}'
        
        if isinstance(self.user, AnonymousUser):
            await self.close()
            return
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        receiver_id = data.get('receiver_id')
        
        # Save to database
        await self.save_message(message, receiver_id)
        
        # Broadcast to chat room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender_id': self.user.id,
                'sender_name': self.user.get_full_name() or self.user.username,
                'timestamp': None  # Will be set by DB
            }
        )
    
    async def chat_message(self, event):
        """Send chat message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'chat',
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'is_mine': event['sender_id'] == self.user.id
        }))
    
    @database_sync_to_async
    def save_message(self, message_text, receiver_id):
        """Save chat message to database"""
        from accounts.models import User
        try:
            request = BloodRequest.objects.get(id=self.request_id)
            receiver = User.objects.get(id=receiver_id)
            
            ChatMessage.objects.create(
                request=request,
                sender=self.user,
                receiver=receiver,
                message=message_text
            )
        except Exception as e:
            print(f"Error saving message: {e}")


class DonorLocationConsumer(AsyncWebsocketConsumer):
    """Handle donor location streaming"""
    
    async def connect(self):
        if isinstance(self.scope['user'], AnonymousUser):
            await self.close()
            return
        
        await self.accept()
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        
        # Broadcast to relevant request tracking rooms
        if data.get('request_id'):
            room_name = f"request_{data['request_id']}"
            await self.channel_layer.group_send(
                room_name,
                {
                    'type': 'send.tracking.update',
                    'data': {
                        'type': 'donor_location',
                        'donor_id': self.scope['user'].id,
                        'latitude': data['latitude'],
                        'longitude': data['longitude'],
                        'timestamp': data.get('timestamp')
                    }
                }
            )
