from django.urls import path
from . import api_views

app_name = 'blood_requests_api'

urlpatterns = [
    # Live requests
    path('requests/live/', api_views.live_requests_api, name='live-requests'),
    
    # Request tracking
    path('requests/<int:request_id>/', api_views.TrackSpecificRequestView.as_view(), name='track-request'),
    path('requests/<int:request_id>/timeline/', api_views.RequestTimelineView.as_view(), name='request-timeline'),
    path('requests/<int:request_id>/responses/', api_views.RequestResponsesView.as_view(), name='request-responses'),
    path('requests/<int:request_id>/analytics/', api_views.RequestAnalyticsView.as_view(), name='request-analytics'),
    path('requests/<int:request_id>/select-donor/', api_views.SelectDonorView.as_view(), name='select-donor'),
    
    # Request actions
    path('requests/<int:request_id>/respond/', api_views.respond_to_request_api, name='respond-to-request'),
    
    # Donor search
    path('donors/find/', api_views.find_donors_api, name='find-donors'),
    
    # Emergency alerts
    path('emergency-alert/', api_views.emergency_alert_api, name='emergency-alert'),
    
    # Chat functionality
    path('chat/history/<int:contact_id>/', api_views.chat_history_api, name='chat-history'),
]
