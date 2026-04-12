"""
ASGI config for blood_donation project.
Adds WebSocket support for real-time notifications using Django Channels.
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blood_donation.settings')

# Initialize Django ASGI application early
django_asgi_app = get_asgi_application()

# Import routing after Django setup
from blood_requests_app import routing as blood_requests_routing
from notifications import routing as notifications_routing

# Combine all WebSocket URL patterns
websocket_urlpatterns = (
    blood_requests_routing.websocket_urlpatterns +
    notifications_routing.websocket_urlpatterns
)

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
