"""
Enhanced API URLs for BloodLife Platform v2.0
Includes all new optimized endpoints
"""
from django.urls import path
from . import enhanced_api_views

urlpatterns = [
    # Public endpoints
    path('requests/active/', enhanced_api_views.get_active_requests, name='api-active-requests'),
    path('requests/stats/', enhanced_api_views.get_request_stats, name='api-request-stats'),
    
    # Authenticated endpoints
    path('user/donation-history/', enhanced_api_views.get_user_donation_history, name='api-user-donation-history'),
    path('requests/<int:request_id>/report-issue/', enhanced_api_views.report_request_issue, name='api-report-issue'),
]
