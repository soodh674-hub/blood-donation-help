"""
URL configuration for enhanced REST API (React web & mobile apps)
"""
from django.urls import path
from .api_enhanced import (
    DashboardStatsView,
    LiveRequestsView,
    DonorSearchView,
    TrackRequestView,
    NotificationsView,
    ChatMessagesView,
    UserProfileView,
    CreateBloodRequestView,
    MyRequestsView,
)

urlpatterns = [
    # Dashboard & Stats
    path('dashboard/stats/', DashboardStatsView.as_view(), name='api-dashboard-stats'),
    path('requests/live/', LiveRequestsView.as_view(), name='api-live-requests'),
    
    # Donor Search
    path('donors/search/', DonorSearchView.as_view(), name='api-donor-search'),
    
    # Request Tracking
    path('requests/<int:request_id>/track/', TrackRequestView.as_view(), name='api-track-request'),
    
    # Notifications
    path('notifications/', NotificationsView.as_view(), name='api-notifications'),
    
    # Chat
    path('requests/<int:request_id>/chat/', ChatMessagesView.as_view(), name='api-chat-messages'),
    
    # User Profile
    path('users/profile/', UserProfileView.as_view(), name='api-user-profile'),
    
    # Blood Requests CRUD
    path('requests/create/', CreateBloodRequestView.as_view(), name='api-create-request'),
    path('requests/my/', MyRequestsView.as_view(), name='api-my-requests'),
]
