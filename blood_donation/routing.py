"""
WebSocket URL routing for Blood Donation app
"""
from django.urls import re_path
from blood_requests_app.consumers import (
    LiveRequestsConsumer,
    RequestTrackingConsumer,
    ChatConsumer,
    DonorLocationConsumer
)

websocket_urlpatterns = [
    # Live requests broadcast to all donors
    re_path(r'ws/requests/live/$', LiveRequestsConsumer.as_asgi()),
    
    # Track specific request (donor locations & status)
    re_path(r'ws/requests/(?P<request_id>\w+)/tracking/$', RequestTrackingConsumer.as_asgi()),
    
    # Chat between donor and requester
    re_path(r'ws/chat/(?P<request_id>\w+)/$', ChatConsumer.as_asgi()),
    
    # Donor location streaming
    re_path(r'ws/donor/location/$', DonorLocationConsumer.as_asgi()),
]
