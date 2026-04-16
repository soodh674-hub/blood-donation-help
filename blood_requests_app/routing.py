"""
WebSocket Routing Configuration
Maps URL patterns to WebSocket consumers
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Chat WebSocket endpoint
    # URL format: ws://domain/ws/chat/{room_name}/
    # room_name should be unique identifier for conversation (e.g., "user1_user2")
    re_path(r'ws/chat/(?P<room_name>[^/]+)/$', consumers.ChatConsumer.as_asgi()),
    
    # Notifications WebSocket endpoint
    # URL format: ws://domain/ws/notifications/
    re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()),
]
