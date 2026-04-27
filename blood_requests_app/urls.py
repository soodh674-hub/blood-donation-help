from django.urls import path, include
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from . import views
from . import views_api
from . import enhanced_views

@api_view(['GET'])
@permission_classes([AllowAny])
def api_status(request):
    """Check if API is working"""
    return JsonResponse({
        'status': 'ok',
        'message': 'Blood Request API is running',
        'endpoints': {
            'create': '/api/requests/create-api/',
            'list': '/api/requests/list/',
            'detail': '/api/requests/{id}/'
        }
    })

urlpatterns = [
    # API Status Check
    path("status/", api_status, name="api-status"),
    
    # API Endpoints
    path("api/", include(('blood_requests_app.api_urls', 'blood_requests_api'), namespace='blood_requests_api')),
    
    # Frontend pages - ORIGINAL TRACK BLOOD REQUEST DASHBOARD (RESTORED)
    path("", views.create_request_unified_page, name="blood-request-create-page"),
    path("create/", views.create_request_unified_page, name="blood-request-create-unified"),
    path("track/<int:request_id>/", views.track_request_dashboard, name="track-request"),
    path("track/", views.track_request_dashboard, name="track-request-dashboard"),
    path("manage/<int:request_id>/", views.manage_request, name="manage-request"),
    path("my-requests/", views.my_requests_page, name="my-blood-requests"),
    
    # OLD create request page (kept for backward compatibility)
    # path("old-create/", views.create_request_page, name="blood-request-create-old"),
    
    # API endpoints (these will be accessed via /api/requests/* due to main urls.py configuration)
    path("create-api/", views.BloodRequestCreateView.as_view(), name="blood-request-create-api"),
    # path("list/", views.BloodRequestListView.as_view(), name="blood-request-list-api"),  # TODO: Implement BloodRequestListView
    # path("<int:pk>/", views.BloodRequestDetailView.as_view(), name="blood-request-detail-api"),  # TODO: Implement BloodRequestDetailView
    
    # OLD Live blood requests (will be replaced)
    path("live-requests/", views.live_blood_requests, name="live-blood-requests"),
    
    # User request tracking endpoints
    path("user-requests/", views_api.UserBloodRequestsView.as_view(), name="user-blood-requests"),
    path("track/<int:request_id>/", views.track_specific_request, name="track-specific-request"),
    path("delete/<int:request_id>/", views.delete_request_permanently, name="delete-request-permanently"),
    
    # ========================================================================
    # NEW ENHANCED API ENDPOINTS FOR REAL-TIME TRACKING SYSTEM
    # ========================================================================
    
    # Get live requests for homepage (enhanced version)
    path("live/", views.get_live_requests, name="get-live-requests"),
    
    # Donor response system
    path("<int:request_id>/respond/", views.respond_to_request, name="respond-to-request"),
    path("<int:request_id>/responses/", views.get_request_responses, name="get-request-responses"),
    
    # Donor selection by requester
    path("select-donor/<int:response_id>/", views.select_donor, name="select-donor"),

    # Donor location tracking
    path("response/<int:response_id>/location/", views.get_donor_location, name="get-donor-location"),
    
    # Location tracking
    path("update-location/", views.update_donor_location, name="update-donor-location"),
    
    # Status updates
    path("update-status/<int:response_id>/", views.update_response_status, name="update-response-status"),
    
    # Donor dashboard
    path("my-responses/", views.get_my_active_responses, name="get-my-responses"),
    
    # ========================================================================
    # NEW REAL-TIME FEATURES (Chat, Ratings, Nearby Donors)
    # ========================================================================
    
    # Nearby donors for a request
    path("<int:request_id>/nearby-donors/", views_api.NearbyDonorsView.as_view(), name='nearby-donors'),
    
    # Chat system
    path("<int:request_id>/chat/", views_api.ChatHistoryView.as_view(), name='chat-history'),
    path("chat/mark-read/", views_api.MarkMessageReadView.as_view(), name='mark-read'),
    path("<int:request_id>/chat/send/", views_api.SendMessageView.as_view(), name='send-message'),  # HTTP fallback
    
    # Chatbot
    path("chatbot/", views_api.ChatbotView.as_view(), name='chatbot'),
    
    # Donor Rating System - Moved to accounts app
    # path('api/rate-donor/', views.rate_donor, name='rate-donor'),
    # path('donor/<int:donor_id>/ratings/', views.donor_ratings, name='donor-ratings'),
    # path('donation-history/', views.my_donation_history, name='donation-history'),
    
    # Donor GPS Location Sharing
    path('donor/<int:response_id>/share-location/', views.donor_gps_sender, name='donor-gps-sender'),
    
    # Donor location and availability
    path("donor/location/", views_api.UpdateDonorLocationView.as_view(), name='donor-location'),
    path("donor/availability/", views_api.ToggleDonorAvailabilityView.as_view(), name='donor-availability'),
    
    # ========================================================================
    # ADMIN VERIFICATION SYSTEM (Phase 3)
    # ========================================================================
    
    # Verification page
    path("admin/verify/", views.verify_requests_page, name='verify-requests-page'),
    
    # Admin camp management
    path("admin/camps/", views.admin_camps_page, name='admin-camps-page'),
    path("admin/camps/create/", views.admin_create_camp, name='admin-create-camp'),
    path("admin/camps/<int:camp_id>/edit/", views.admin_edit_camp, name='admin-edit-camp'),
    path("admin/camps/<int:camp_id>/delete/", views.admin_delete_camp, name='admin-delete-camp'),
    
    # User-facing campaigns
    path("campaigns/", views.campaign_list, name='campaign-list'),
    path("campaigns/create/", views.campaign_create, name='campaign-create'),
    path("campaigns/<int:campaign_id>/join/", views.campaign_join, name='campaign-join'),
    
    # Verification API endpoint
    path("<int:request_id>/verify/", views.verify_request_api, name='verify-request-api'),
    
    # ========================================================================
    # PHASE 4: DONOR ACCEPT REQUEST
    # ========================================================================
    
    # Accept blood request (creates response and redirects to tracking)
    path("<int:request_id>/accept/", views.accept_request_view, name='accept-request'),
    
    # ========================================================================
    # CHAT SYSTEM (Instagram-style Direct Messaging)
    # ========================================================================
    
    # Chat inbox
    path("chat/", views.chat_inbox, name='chat-inbox'),
    
    # Manage all requests
    path("manage-all/", views.manage_all_requests, name='manage-all-requests'),
    
    # Chat conversation with specific user
    path("chat/<int:user_id>/", views.chat_conversation, name='chat-conversation'),
    
    # Start chat with donor (from donor search profile)
    path("chat/start/<int:donor_id>/", views.start_chat_with_donor, name='start-chat-with-donor'),
    
    # Send chat message (AJAX)
    path("chat/api/send/", views.send_chat_message, name='chat-send'),
    
    # Mark messages as read (AJAX)
    path("chat/api/mark-read/", views.mark_messages_read, name='chat-mark-read'),
    
    # Get unread chat count (for navbar badge)
    path("chat/api/unread-count/", views.unread_chat_count_api, name='unread-chat-count'),
    
    # ========================================================================
    # BLOOD REQUEST WORKFLOW APIs (Complete 20-step process)
    # ========================================================================
    
    # Activate request and notify donors (Steps 1-6)
    path("<int:request_id>/activate/", views.activate_request_api, name='activate-request'),
    
    # Donor accept/decline request (Steps 7-10)
    path("<int:request_id>/accept/", views.accept_request_api, name='accept-request-api'),
    path("<int:request_id>/decline/", views.decline_request_api, name='decline-request'),
    
    # Update donor status (Steps 13-14)
    path("response/<int:response_id>/update-status/", views.update_donor_status_api, name='update-donor-status'),
    
    # Contact sharing (Step 11)
    path("response/<int:response_id>/contact/", views.get_contact_details_api, name='get-contact-details'),
    
    # Cancel request (Step 17)
    path("<int:request_id>/cancel/", views.cancel_request_api, name='cancel-request-api'),
    
    # Request history (Step 18)
    path("<int:request_id>/history/", views.get_request_history_api, name='request-history'),
    
    # Donor location tracking
    path("donor/update-location/", views.update_donor_location_api, name='update-donor-location-api'),
    
    # Get nearby requests for donors
    path("nearby-requests/", views.get_nearby_requests_api, name='nearby-requests'),
]


