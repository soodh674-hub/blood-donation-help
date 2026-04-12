from django.urls import path, include
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from . import views
from . import views_api

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
    
    # Frontend pages - UNIFIED REQUEST CREATION (NEW)
    path("", views.create_request_unified_page, name="blood-request-create-page"),
    path("create/", views.create_request_unified_page, name="blood-request-create-unified"),
    path("track/", views.track_request_dashboard, name="track-request-dashboard"),
    path("my-requests/", views.my_requests_page, name="my-blood-requests"),
    
    # OLD create request page (kept for backward compatibility)
    # path("old-create/", views.create_request_page, name="blood-request-create-old"),
    
    # API endpoints (these will be accessed via /api/requests/* due to main urls.py configuration)
    path("create-api/", views.BloodRequestCreateView.as_view(), name="blood-request-create-api"),
    path("list/", views.BloodRequestListView.as_view(), name="blood-request-list-api"),
    path("<int:pk>/", views.BloodRequestDetailView.as_view(), name="blood-request-detail-api"),
    
    # OLD Live blood requests (will be replaced)
    path("live-requests/", views.live_blood_requests, name="live-blood-requests"),
    
    # User request tracking endpoints
    path("user-requests/", views_api.UserBloodRequestsView.as_view(), name="user-blood-requests"),
    path("track/<int:request_id>/", views_api.TrackSpecificRequestView.as_view(), name="track-specific-request"),
    
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
    
    # Rating system
    path("rate-user/", views_api.RateUserView.as_view(), name='rate-user'),
    
    # Donor location and availability
    path("donor/location/", views_api.UpdateDonorLocationView.as_view(), name='donor-location'),
    path("donor/availability/", views_api.ToggleDonorAvailabilityView.as_view(), name='donor-availability'),
    
    # ========================================================================
    # ADMIN VERIFICATION SYSTEM (Phase 3)
    # ========================================================================
    
    # Verification page
    path("admin/verify/", views.verify_requests_page, name='verify-requests-page'),
    
    # Verification API endpoint
    path("<int:request_id>/verify/", views.verify_request_api, name='verify-request-api'),
    
    # ========================================================================
    # PHASE 4: DONOR ACCEPT REQUEST
    # ========================================================================
    
    # Accept blood request (creates response and redirects to tracking)
    path("<int:request_id>/accept/", views.accept_request_view, name='accept-request'),
]


