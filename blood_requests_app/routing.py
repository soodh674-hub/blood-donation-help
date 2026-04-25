"""
WebSocket Routing Configuration
Maps URL patterns to WebSocket consumers
"""
from django.urls import re_path, path
from . import consumers

websocket_urlpatterns = [
    # Chat WebSocket endpoint
    # URL format: ws://domain/ws/chat/{room_name}/
    # room_name should be unique identifier for conversation (e.g., "user1_user2")
    path('ws/chat/<str:room_name>/', consumers.ChatConsumer.as_asgi()),
    
    # Notifications WebSocket endpoint
    # URL format: ws://domain/ws/notifications/
    path('ws/notifications/', consumers.NotificationConsumer.as_asgi()),
]
