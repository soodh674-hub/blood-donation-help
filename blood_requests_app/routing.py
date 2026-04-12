from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Live blood requests broadcast
    re_path(r'ws/requests/live/$', consumers.LiveRequestsConsumer.as_asgi()),
    
    # Individual request tracking
    re_path(r'ws/request/(?P<request_id>\w+)/$', consumers.RequestTrackingConsumer.as_asgi()),
    
    # Chat room
    re_path(r'ws/chat/(?P<request_id>\w+)/$', consumers.ChatConsumer.as_asgi()),
    
    # Donor location updates
    re_path(r'ws/donor/location/$', consumers.DonorLocationConsumer.as_asgi()),
]
