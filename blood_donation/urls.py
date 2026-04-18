"""URL Configuration for blood_donation project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.http import HttpResponse
from django.shortcuts import render
from accounts import views as accounts_views
from blood_requests_app import views as blood_request_views
from accounts import health_check

# Try to import JWT views - make optional to prevent deployment crashes
try:
    from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    TokenObtainPairView = None
    TokenRefreshView = None
    TokenVerifyView = None

def home_view(request):
    """Modern BloodLife dashboard homepage with real-time features"""
    from blood_requests_app.models import BloodRequest
    from django.utils import timezone
    
    # Get active blood requests for the live feed - prioritize by recency and priority
    blood_requests = BloodRequest.objects.filter(
        status__in=['active', 'approved', 'pending']
    ).order_by(
        '-created_at'
    )[:20]
    
    context = {
        'blood_requests': blood_requests,
        'unread_notifications': 0,
    }
    
    if request.user.is_authenticated:
        try:
            from notifications.models import Notification
            context['unread_notifications'] = int(Notification.objects.filter(
                user=request.user, 
                is_read=False
            ).count())
        except Exception as e:
            # Silently fail to prevent recursion errors
            context['unread_notifications'] = 0
    
    return render(request, 'home.html', context)


def how_it_works_view(request):
    """How It Works page"""
    return render(request, 'pages/how_it_works.html')


def about_view(request):
    """About Us page"""
    return render(request, 'pages/about.html')


def favicon(request):
    """Serve favicon.ico to prevent 404 errors"""
    import os
    from django.conf import settings
    from django.http import HttpResponse, Http404
    
    # Try to serve the static favicon.ico file first
    favicon_path = os.path.join(settings.BASE_DIR, 'static', 'favicon.ico')
    if os.path.exists(favicon_path):
        try:
            with open(favicon_path, 'rb') as f:
                favicon_data = f.read()
            return HttpResponse(favicon_data, content_type='image/x-icon')
        except Exception as e:
            # If there's an error reading the file, fall back to the embedded favicon
            pass
    
    # Fallback to embedded favicon if file not found
    favicon_content = b'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQEAYAAABPYyMiAAAABmJLR0T///////8JWPfcAAAACXBIWXMAAABIAAAASABGyWs+AAAAF0lEQVRIx2NgGAWjYBSMglEwCkbBSAcAAL//BR8RKw4AAAAASUVORK5CYII='
    import base64
    import binascii
    try:
        img_data = base64.b64decode(favicon_content)
        return HttpResponse(img_data, content_type="image/x-icon")
    except binascii.Error:
        # In case of decode error, return a minimal empty response
        return HttpResponse(b'', content_type="image/x-icon")

def robots_txt(request):
    """Serve robots.txt to prevent 404 errors"""
    content = "User-agent: *\nDisallow: /admin/\nDisallow: /api/\nDisallow: /secure-admin-panel-x92/\nAllow: /\nSitemap: https://bloodis-life.online/sitemap.xml\n"
    return HttpResponse(content, content_type="text/plain")

def security_txt(request):
    """Serve security.txt to prevent 404 errors"""
    content = "Contact: mailto:soodh674@gmail.com\n"
    return HttpResponse(content, content_type="text/plain")

def ads_txt(request):
    """Serve ads.txt to prevent 404 errors from ad bots"""
    # Return empty or minimal ads.txt (we don't use ads)
    content = "# No advertising on this site\n"
    return HttpResponse(content, content_type="text/plain")

def catchall_handler(request, *args, **kwargs):
    """Catch-all handler for common endpoints that might be scanned"""
    # Common paths that get scanned by bots
    if request.path.startswith('/server') or request.path.startswith('/console') or request.path.startswith('/adminer'):
        # Return 404-like response but without actual 404 log
        return HttpResponse("Not Found", status=200)
    else:
        # For other unknown paths, return a 404
        return HttpResponse("Not Found", status=404)

urlpatterns = [
    # Public home page - NEW REDESIGNED VERSION WITH FEATURE PREVIEWS
    path('', home_view, name='home'),
    
    # CAPTCHA URLs (must be included for django-simple-captcha to work)
    path('captcha/', include('captcha.urls')),
    
    # How It Works page
    path('how-it-works/', how_it_works_view, name='how-it-works'),
    
    # About Us page
    path('about/', about_view, name='about'),
    
    # Sitemap for SEO
    path('sitemap.xml', TemplateView.as_view(template_name='sitemap.xml', content_type='text/xml'), name='sitemap'),
    
    # Favicon handler to prevent 404 errors
    path('favicon.ico', favicon, name='favicon'),
    
    # Additional handlers to prevent 404 errors from scanners
    path('robots.txt', robots_txt, name='robots_txt'),
    path('.well-known/security.txt', security_txt, name='security_txt'),
    path('ads.txt', ads_txt, name='ads_txt'),
    
    # Health check endpoint (root level for easy monitoring)
    path('health/', health_check.health_check, name='health-check'),
    
    # Admin panel - hidden URL for security
    path('secure-admin-panel-x92/', admin.site.urls),
    
    # Admin verification system (Phase 3)
    path('admin/verify/', blood_request_views.verify_requests_page, name='admin-verify-requests'),
    path('secure-admin-panel-x92/verify/', blood_request_views.verify_requests_page, name='admin-verify-requests-panel'),
    path('api/admin/verify/<int:request_id>/', blood_request_views.verify_request_api, name='admin-verify-request-api'),
    
    # Direct registration route (common access pattern)
    path('register/', accounts_views.donor_registration_view, name='register-direct'),  # Allows /register/ to work directly
    
    # Direct API routes for easier access
    path('api/profile/update/', accounts_views.update_profile, name='api-profile-update'),
    path('api/users/<int:user_id>/', accounts_views.user_detail_api, name='api-user-detail'),
    
    # Frontend pages
    path('auth/', include('allauth.urls')),  # Django allauth for email verification
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    path('search/', include(('accounts.urls', 'accounts'), namespace='accounts_search')),  # Search functionality
    path('requests/', include(('blood_requests_app.urls', 'requests'), namespace='requests')),  # Handles blood requests
    path('notifications/', include('notifications.urls', namespace='notifications')),
    path('donors/', include(('donors.urls', 'donors'), namespace='donors')),  # Donor pages
    
    # Authentication API (JWT - if available)
    *([
        path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
        path('api/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    ] if JWT_AVAILABLE else []),
    
    # Core Apps APIs
    path('api/accounts/', include(('accounts.urls', 'accounts_api'), namespace='accounts_api')),
    path('api/donors/', include(('donors.urls', 'donors_api'), namespace='donors_api')),
    path('api/requests/', include(('blood_requests_app.urls', 'blood_requests_api_v1'), namespace='blood_requests_api_v1')),
    path('api/notifications/', include('notifications.urls', namespace='api_notifications')),
    path('api/analytics/', include('analytics.urls')),
    
    # Enhanced REST API for React Web & Mobile Apps
    path('api/v2/', include('blood_requests_app.api_urls_enhanced')),
    
    # NEW: Enhanced API v2.0 with optimizations
    path('api/v2/enhanced/', include('blood_requests_app.enhanced_api_urls')),
]

# Static and media files
# In production, WhiteNoise serves static files, but we still need this for development
# and for serving files during development
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Admin site customization
admin.site.site_header = "Blood Donation Platform Admin"
admin.site.site_title = "Blood Donation Admin Portal"
admin.site.index_title = "Welcome to Blood Donation Platform Administration"

# Catch-all for common scanner endpoints (must be last)
urlpatterns.append(path('<path:path>', catchall_handler))