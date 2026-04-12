"""
WebSocket consumer for real-time notifications
Handles live notification delivery to connected users
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from django.utils import timezone


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time notifications
    
    Features:
    - Connect to notification stream
    - Receive instant notifications
    - Mark notifications as read in real-time
    - Disconnect gracefully
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        if self.scope["user"].is_anonymous:
            # Reject anonymous connections
            await self.close()
        else:
            # Create unique room name for user
            self.room_group_name = f'notifications_{self.scope["user"].id}'
            
            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            await self.accept()
            
            # Send welcome message
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'message': 'Connected to notification stream',
                'timestamp': timezone.now().isoformat()
            }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave room group
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """
        Receive message from WebSocket
        
        Expected actions:
        - mark_read: Mark notification as read
        - get_unread: Get unread count
        """
        data = json.loads(text_data)
        action = data.get('action')
        
        if action == 'mark_read':
            notification_id = data.get('notification_id')
            if notification_id:
                await self.mark_notification_read(notification_id)
        elif action == 'get_unread':
            await self.send_unread_count()
    
    async def send_notification(self, event):
        """
        Send notification to WebSocket client
        
        Event format:
        {
            'type': 'send_notification',
            'notification': {
                'id': 123,
                'title': 'New Blood Request',
                'message': 'O+ blood needed urgently',
                'notification_type': 'blood_request',
                'created_at': '2026-03-08T12:00:00Z'
            }
        }
        """
        notification = event['notification']
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'new_notification',
            'notification': notification
        }))
    
    async def notification_update(self, event):
        """
        Send notification update (count change)
        
        Event format:
        {
            'type': 'notification_update',
            'unread_count': 5
        }
        """
        await self.send(text_data=json.dumps({
            'type': 'update',
            'unread_count': event['unread_count']
        }))
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Mark a notification as read"""
        from .models import Notification
        
        try:
            notification = Notification.objects.get(
                id=notification_id,
                user=self.scope["user"]
            )
            notification.is_read = True
            notification.save()
            
            # Send updated count
            self.send_unread_count_sync()
        except Notification.DoesNotExist:
            pass
    
    @sync_to_async
    def send_unread_count_sync(self):
        """Send unread count after marking as read"""
        self.send_unread_count()
    
    async def send_unread_count(self):
        """Get and send unread notification count"""
        count = await self.get_unread_count_db()
        
        await self.send(text_data=json.dumps({
            'type': 'unread_count',
            'count': count
        }))
    
    @database_sync_to_async
    def get_unread_count_db(self):
        """Get unread count from database"""
        from .models import Notification
        
        return Notification.objects.filter(
            user=self.scope["user"],
            is_read=False
        ).count()


# Utility function to send notifications via Django signals
async def send_notification_to_user(user, notification_data):
    """
    Send real-time notification to a specific user
    
    Usage:
    from notifications.consumers import send_notification_to_user
    
    await send_notification_to_user(user, {
        'id': notification.id,
        'title': notification.title,
        'message': notification.message,
        'notification_type': notification.notification_type,
        'created_at': notification.created_at.isoformat()
    })
    """
    from channels.layers import get_channel_layer
    
    channel_layer = get_channel_layer()
    room_group_name = f'notifications_{user.id}'
    
    await channel_layer.group_send(
        room_group_name,
        {
            'type': 'send_notification',
            'notification': notification_data
        }
    )


async def broadcast_notification_update(user):
    """
    Broadcast unread count update to user's connected clients
    
    Usage:
    from notifications.consumers import broadcast_notification_update
    
    await broadcast_notification_update(user)
    """
    from channels.layers import get_channel_layer
    from .models import Notification
    
    channel_layer = get_channel_layer()
    room_group_name = f'notifications_{user.id}'
    
    unread_count = Notification.objects.filter(
        user=user,
        is_read=False
    ).count()
    
    await channel_layer.group_send(
        room_group_name,
        {
            'type': 'notification_update',
            'unread_count': unread_count
        }
    )
