"""
WebSocket Consumers for Real-Time Chat
Handles live messaging between users
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.contrib.auth import get_user_model
from blood_requests_app.models_chat import ChatMessage

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time chat
    Handles:
    - Connection/authentication
    - Message sending/receiving
    - Read receipts
    - Typing indicators
    - Online status
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        
        # Get user from session
        self.user = self.scope.get("user", None)
        
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to chat',
            'user_id': self.user.id,
            'username': self.user.username
        }))
        
        # Notify others that user is online
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'action': 'online',
                'user_id': self.user.id,
                'username': self.user.username
            }
        )
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, 'room_group_name'):
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            
            # Notify others that user is offline
            if self.user and self.user.is_authenticated:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'user_status',
                        'action': 'offline',
                        'user_id': self.user.id,
                        'username': self.user.username
                    }
                )
    
    async def receive(self, text_data):
        """Handle incoming message"""
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type', 'message')
        
        if message_type == 'message':
            # Handle chat message
            message = text_data_json.get('message', '').strip()
            receiver_id = text_data_json.get('receiver_id')
            
            if not message or not receiver_id:
                return
            
            # Save message to database
            chat_message = await self.save_message(
                sender=self.user,
                receiver_id=receiver_id,
                message=message
            )
            
            # Broadcast message to room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender_id': self.user.id,
                    'sender_username': self.user.username,
                    'receiver_id': receiver_id,
                    'timestamp': chat_message.created_at.isoformat(),
                    'message_id': chat_message.id
                }
            )
        
        elif message_type == 'typing':
            # Handle typing indicator
            is_typing = text_data_json.get('is_typing', False)
            receiver_id = text_data_json.get('receiver_id')
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'is_typing': is_typing,
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'receiver_id': receiver_id
                }
            )
        
        elif message_type == 'read_receipt':
            # Handle read receipt
            message_ids = text_data_json.get('message_ids', [])
            
            # Mark messages as read
            await self.mark_messages_read(message_ids)
            
            # Notify sender that messages were read
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'read_receipt',
                    'message_ids': message_ids,
                    'reader_id': self.user.id,
                    'username': self.user.username
                }
            )
    
    async def chat_message(self, event):
        """Send chat message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            'receiver_id': event['receiver_id'],
            'timestamp': event['timestamp'],
            'message_id': event['message_id']
        }))
    
    async def user_status(self, event):
        """Send user online/offline status"""
        await self.send(text_data=json.dumps({
            'type': 'user_status',
            'action': event['action'],
            'user_id': event['user_id'],
            'username': event['username']
        }))
    
    async def typing_indicator(self, event):
        """Send typing indicator"""
        if event['receiver_id'] == self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing_indicator',
                'is_typing': event['is_typing'],
                'user_id': event['user_id'],
                'username': event['username']
            }))
    
    async def read_receipt(self, event):
        """Send read receipt"""
        await self.send(text_data=json.dumps({
            'type': 'read_receipt',
            'message_ids': event['message_ids'],
            'reader_id': event['reader_id'],
            'username': event['username']
        }))
    
    @database_sync_to_async
    def save_message(self, sender, receiver_id, message):
        """Save message to database (async-safe)"""
        receiver = User.objects.get(id=receiver_id)
        
        chat_message = ChatMessage.objects.create(
            sender=sender,
            receiver=receiver,
            message=message,
            created_at=timezone.now()
        )
        
        # Create notification for receiver
        try:
            from notifications.models import Notification
            Notification.objects.create(
                user=receiver,
                notification_type='chat_message',
                title=f'New message from {sender.get_full_name() or sender.username}',
                message=message[:100] + ('...' if len(message) > 100 else ''),
                priority='medium'
            )
        except Exception as e:
            print(f"Error creating notification: {str(e)}")
        
        return chat_message
    
    @database_sync_to_async
    def mark_messages_read(self, message_ids):
        """Mark messages as read (async-safe)"""
        ChatMessage.objects.filter(
            id__in=message_ids,
            receiver=self.user
        ).update(is_read=True, read_at=timezone.now())


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time notifications
    Handles:
    - Connection/authentication
    - Notification delivery
    - Unread count updates
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.user = self.scope.get("user", None)
        
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return
        
        self.group_name = f'notifications_{self.user.id}'
        
        # Join notification group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial unread count
        unread_count = await self.get_unread_count()
        
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'unread_count': unread_count
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Handle incoming message"""
        text_data_json = json.loads(text_data)
        
        if text_data_json.get('type') == 'mark_all_read':
            # Mark all notifications as read
            await self.mark_all_notifications_read()
            
            await self.send(text_data=json.dumps({
                'type': 'all_marked_read',
                'message': 'All notifications marked as read'
            }))
    
    async def send_notification(self, event):
        """Send notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'id': event.get('id'),
            'title': event['title'],
            'message': event['message'],
            'notification_type': event['notification_type'],
            'priority': event.get('priority', 'medium'),
            'timestamp': event.get('timestamp'),
            'url': event.get('url')
        }))
        
        # Send updated unread count
        unread_count = await self.get_unread_count()
        await self.send(text_data=json.dumps({
            'type': 'unread_count_update',
            'unread_count': unread_count
        }))
    
    async def unread_count_update(self, event):
        """Send unread count update"""
        await self.send(text_data=json.dumps({
            'type': 'unread_count_update',
            'unread_count': event['unread_count']
        }))
    
    @database_sync_to_async
    def get_unread_count(self):
        """Get unread notification count (async-safe)"""
        try:
            from notifications.models import Notification
            return Notification.objects.filter(
                user=self.user,
                is_read=False
            ).count()
        except:
            return 0
    
    @database_sync_to_async
    def mark_all_notifications_read(self):
        """Mark all notifications as read (async-safe)"""
        try:
            from notifications.models import Notification
            Notification.objects.filter(
                user=self.user,
                is_read=False
            ).update(is_read=True)
        except Exception as e:
            print(f"Error marking notifications read: {str(e)}")
