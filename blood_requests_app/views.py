from rest_framework import generics, permissions, filters, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
import logging

from .models import BloodRequest
from .serializers import (
    BloodRequestSerializer,
    BloodRequestCreateSerializer,
    BloodRequestDetailSerializer,
)

# Setup logging
logger = logging.getLogger(__name__)


def time_ago(dt):
    """
    Helper function to convert datetime to human-readable time ago format.
    """
    now = timezone.now()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return 'Just now'
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f'{minutes} minute{"s" if minutes > 1 else ""} ago'
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f'{hours} hour{"s" if hours > 1 else ""} ago'
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f'{days} day{"s" if days > 1 else ""} ago'
    else:
        weeks = int(seconds / 604800)
        return f'{weeks} week{"s" if weeks > 1 else ""} ago'


def create_request_unified_page(request):
    """
    Blood request creation page - handles both GET and POST
    Uses original stable form with full functionality
    """
    if not request.user.is_authenticated:
        return redirect('/accounts/login/?next=/requests/create/')
    
    # Handle POST request (form submission)
    if request.method == 'POST':
        try:
            logger.info('🟡 Processing blood request creation')
            
            # Extract form data
            data = {
                'patient_name': request.POST.get('patient_name'),
                'patient_age': request.POST.get('patient_age'),
                'patient_blood_group': request.POST.get('patient_blood_group'),
                'required_units': request.POST.get('required_units'),
                'reason': request.POST.get('reason'),
                'priority': request.POST.get('priority', 'normal'),
                'required_by': request.POST.get('required_by'),
                'hospital_name': request.POST.get('hospital_name'),
                'city': request.POST.get('city'),
                'state': request.POST.get('state'),
                'pincode': request.POST.get('pincode', '110001'),
                'contact_person': request.POST.get('contact_person'),
                'contact_phone': request.POST.get('contact_phone'),
                'contact_email': request.POST.get('contact_email'),
                'requester_type': 'individual',
                'latitude': 28.6139,  # Default Delhi coordinates
                'longitude': 77.2090,
            }
            
            # Validate required fields
            required_fields = ['patient_name', 'patient_age', 'patient_blood_group', 
                             'required_units', 'reason', 'required_by', 'hospital_name',
                             'city', 'state', 'contact_person', 'contact_phone', 'contact_email']
            
            missing_fields = [f for f in required_fields if not data.get(f)]
            if missing_fields:
                logger.error(f'Missing required fields: {missing_fields}')
                from django.contrib import messages
                messages.error(request, f'Missing required fields: {", ".join(missing_fields)}')
                return render(request, 'requests/create_request.html')
            
            # Create serializer and validate
            from .serializers import BloodRequestCreateSerializer
            serializer = BloodRequestCreateSerializer(data=data)
            
            if serializer.is_valid():
                # Save the request
                blood_request = serializer.save(requester=request.user)
                logger.info(f'✅ Blood request created by user: {request.user.id}')
                
                # Send notifications
                try:
                    from notifications.services import BloodRequestNotificationService
                    notification_service = BloodRequestNotificationService()
                    
                    if blood_request.priority == 'emergency':
                        notifications_sent = notification_service.send_emergency_notification(blood_request)
                    else:
                        notifications_sent = notification_service.send_blood_request_notification(
                            blood_request, 
                            limit=50
                        )
                    
                    logger.info(f'📧 Sent {notifications_sent} notifications for request {blood_request.id}')
                except Exception as notif_error:
                    logger.error(f'Failed to send notifications: {str(notif_error)}', exc_info=True)
                
                # Redirect to success
                from django.shortcuts import redirect
                from django.contrib import messages
                messages.success(request, '✅ Blood request created successfully! Donors will be notified.')
                return redirect('/')
            else:
                # Validation errors
                logger.error(f'Form validation errors: {serializer.errors}')
                from django.contrib import messages
                error_messages = []
                for field, errors in serializer.errors.items():
                    error_messages.append(f'{field}: {", ".join(errors)}')
                messages.error(request, f'Validation errors: {" | ".join(error_messages)}')
                return render(request, 'requests/create_request.html')
        
        except Exception as e:
            logger.error(f'❌ Error processing POST request: {str(e)}', exc_info=True)
            from django.contrib import messages
            messages.error(request, f'Error creating request: {str(e)}')
            return render(request, 'requests/create_request.html')
    
    # GET request - just render the form with auto-filled user data
    context = {
        'user_name': request.user.get_full_name() or request.user.username,
        'user_phone': getattr(request.user, 'phone', '') or '',
        'user_email': request.user.email,
        'user_city': getattr(request.user, 'city', '') or '',
        'user_state': getattr(request.user, 'state', '') or '',
        'user_pincode': getattr(request.user, 'pincode', '') or '',
    }
    return render(request, 'requests/create_request.html', context)


def track_request_dashboard(request):
    """
    Advanced unified tracking dashboard for blood requests
    Shows all user's requests with management features
    """
    if not request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect('/accounts/login/?next=/requests/track/')
    
    return render(request, 'requests/track_request_dashboard.html')


class BloodRequestCreateView(generics.CreateAPIView):
    """
    Create a new blood request.
    Now allows anonymous submissions with phone verification.
    """

    queryset = BloodRequest.objects.all()
    serializer_class = BloodRequestCreateSerializer
    permission_classes = [AllowAny]  # Changed to allow anonymous users

    def perform_create(self, serializer):
        try:
            # Extract pincode from request data and set defaults if not provided
            pincode = serializer.validated_data.get('pincode', '')
            if not pincode or pincode.strip() == '':
                # Set a default pincode if not provided
                serializer.validated_data['pincode'] = '110001'  # Default Delhi pincode
            
            # Handle authenticated vs anonymous users
            if self.request.user.is_authenticated:
                instance = serializer.save(requester=self.request.user)
                logger.info(f'Blood request created by user: {self.request.user.id}')
                
                # Send notifications to compatible donors
                try:
                    from notifications.services import BloodRequestNotificationService
                    notification_service = BloodRequestNotificationService()
                    
                    if instance.priority == 'emergency':
                        notifications_sent = notification_service.send_emergency_notification(instance)
                    else:
                        notifications_sent = notification_service.send_blood_request_notification(instance)
                    
                    logger.info(f'Sent {notifications_sent} notifications for blood request {instance.id}')
                except Exception as notif_error:
                    logger.error(f'Failed to send notifications: {str(notif_error)}', exc_info=True)
                    # Continue even if notification fails - don't crash the request
            else:
                # For anonymous users, create with minimal info
                # Auto-set status to pending approval for verification
                instance = serializer.save(
                    status='pending'  # Requires admin approval for anonymous submissions
                )
                logger.info(f'Blood request created anonymously: {instance.id}')
                
                # ALSO send notifications for anonymous requests (after approval they'll become active)
                try:
                    from notifications.services import BloodRequestNotificationService
                    notification_service = BloodRequestNotificationService()
                    
                    # Send to limited number of donors for anonymous requests
                    notifications_sent = notification_service.send_blood_request_notification(instance, limit=20)
                    logger.info(f'Sent {notifications_sent} notifications for anonymous request {instance.id}')
                except Exception as notif_error:
                    logger.error(f'Failed to send notifications for anonymous request: {str(notif_error)}', exc_info=True)
                
        except Exception as e:
            logger.error(f'Error creating blood request: {str(e)}', exc_info=True)
            raise


class BloodRequestListView(generics.ListAPIView):
    """
    List blood requests with basic filtering.
    """

    queryset = BloodRequest.objects.all()
    serializer_class = BloodRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status", "priority", "city", "patient_blood_group"]
    ordering_fields = ["created_at", "required_by", "priority"]
    ordering = ["-created_at"]


class BloodRequestDetailView(generics.RetrieveAPIView):
    """
    Retrieve full details of a blood request, including matches.
    """

    queryset = BloodRequest.objects.all()
    serializer_class = BloodRequestDetailSerializer
    permission_classes = [permissions.AllowAny]  # Allow anyone to view requests


def create_request_page(request):
    """Render the blood request creation page with hybrid form handling"""
    
    # Handle traditional POST submission (fallback from JavaScript)
    if request.method == 'POST':
        try:
            logger.info('🟡 Traditional POST form submission detected')
            
            # Extract form data
            data = {
                'patient_name': request.POST.get('patient_name'),
                'patient_age': request.POST.get('patient_age'),
                'patient_blood_group': request.POST.get('patient_blood_group'),
                'required_units': request.POST.get('required_units'),
                'reason': request.POST.get('reason'),
                'priority': request.POST.get('priority', 'normal'),
                'required_by': request.POST.get('required_by'),
                'hospital_name': request.POST.get('hospital_name'),
                'city': request.POST.get('city'),
                'state': request.POST.get('state'),
                'pincode': request.POST.get('pincode', '110001'),
                'contact_person': request.POST.get('contact_person'),
                'contact_phone': request.POST.get('contact_phone'),
                'contact_email': request.POST.get('contact_email'),
                'requester_type': 'individual',
                'latitude': 28.6139,  # Default Delhi coordinates
                'longitude': 77.2090,
            }
            
            # Validate required fields
            required_fields = ['patient_name', 'patient_age', 'patient_blood_group', 
                             'required_units', 'reason', 'required_by', 'hospital_name',
                             'city', 'state', 'contact_person', 'contact_phone', 'contact_email']
            
            missing_fields = [f for f in required_fields if not data.get(f)]
            if missing_fields:
                logger.error(f'Missing required fields: {missing_fields}')
                from django.contrib import messages
                messages.error(request, f'Missing required fields: {", ".join(missing_fields)}')
                return render(request, 'requests/create_request.html')
            
            # Create serializer and validate
            from .serializers import BloodRequestCreateSerializer
            serializer = BloodRequestCreateSerializer(data=data)
            
            if serializer.is_valid():
                # Save the request
                if request.user.is_authenticated:
                    blood_request = serializer.save(requester=request.user)
                    logger.info(f'✅ Blood request created via POST by user: {request.user.id}')
                else:
                    blood_request = serializer.save(status='pending')
                    logger.info(f'✅ Blood request created via POST anonymously')
                
                # Send notifications
                try:
                    from notifications.services import BloodRequestNotificationService
                    notification_service = BloodRequestNotificationService()
                    
                    if blood_request.priority == 'emergency':
                        notifications_sent = notification_service.send_emergency_notification(blood_request)
                    else:
                        notifications_sent = notification_service.send_blood_request_notification(
                            blood_request, 
                            limit=20 if not request.user.is_authenticated else 50
                        )
                    
                    logger.info(f'📧 Sent {notifications_sent} notifications for request {blood_request.id}')
                except Exception as notif_error:
                    logger.error(f'Failed to send notifications: {str(notif_error)}', exc_info=True)
                
                # Redirect to success
                from django.shortcuts import redirect
                from django.contrib import messages
                messages.success(request, '✅ Blood request created successfully! Donors will be notified.')
                return redirect('/')
            else:
                # Validation errors
                logger.error(f'Form validation errors: {serializer.errors}')
                from django.contrib import messages
                error_messages = []
                for field, errors in serializer.errors.items():
                    error_messages.append(f'{field}: {", ".join(errors)}')
                messages.error(request, f'Validation errors: {" | ".join(error_messages)}')
                return render(request, 'requests/create_request.html')
        
        except Exception as e:
            logger.error(f'❌ Error processing POST request: {str(e)}', exc_info=True)
            from django.contrib import messages
            messages.error(request, f'Error creating request: {str(e)}')
            return render(request, 'requests/create_request.html')
    
    # GET request - just render the form
    return render(request, 'requests/create_request.html')


def my_requests_page(request):
    """Redirect to the advanced unified tracking dashboard"""
    from django.shortcuts import redirect
    
    if not request.user.is_authenticated:
        return redirect('/accounts/login/?next=/requests/track/')
    
    # Redirect to the new unified tracking system
    return redirect('/requests/track/')


@api_view(['GET'])
@permission_classes([AllowAny])
def live_blood_requests(request):
    """
    API endpoint to fetch live/active blood requests for homepage display.
    Returns recent active requests from OTHER users (privacy: exclude current user's requests).
    Ordered by urgency and creation time.
    """
    try:
        # Debug: Check total requests in database
        total_requests = BloodRequest.objects.count()
        logger.info(f'Total blood requests in database: {total_requests}')
        
        # Get active, non-expired requests (more inclusive filter)
        now = timezone.now()
        
        # Start with base queryset
        queryset = BloodRequest.objects.filter(
            status__in=['active', 'approved', 'pending', 'partially_fulfilled'],
            expires_at__gt=now,
        )
        
        # PRIVACY: Exclude current user's own requests
        if request.user.is_authenticated:
            queryset = queryset.exclude(requester=request.user)
            logger.info(f'Excluding user {request.user.id}\'s requests from homepage')
        
        live_requests = queryset.order_by(
            '-priority',
            '-created_at'
        )[:10]  # Limit to 10 most recent
        
        # If no results, try without expiration filter (for debugging)
        if not live_requests.exists():
            logger.warning('No active requests found with expiration filter, trying without it...')
            queryset = BloodRequest.objects.filter(
                status__in=['active', 'approved', 'pending', 'partially_fulfilled']
            )
            
            # PRIVACY: Also exclude in fallback query
            if request.user.is_authenticated:
                queryset = queryset.exclude(requester=request.user)
            
            live_requests = queryset.order_by(
                '-priority',
                '-created_at'
            )[:10]
        
        logger.info(f'Found {live_requests.count()} live blood requests')
        
        # Serialize data manually for custom format
        data = []
        for req in live_requests:
            data.append({
                'id': req.id,
                'blood_group': req.patient_blood_group,
                'location': f"{req.city}, {req.state}",
                'urgency': req.priority,
                'urgency_display': req.get_priority_display(),
                'hospital': req.hospital_name,
                'required_units': req.required_units,
                'fulfilled_units': req.fulfilled_units,
                'remaining_units': req.remaining_units,
                'contact_phone': req.contact_phone,
                'created_at': req.created_at.isoformat(),
                'time_ago': time_ago(req.created_at),
                'is_critical': req.is_critical,
            })
        
        logger.info(f'Live blood requests fetched: {len(data)} active requests')
        return Response(data)
        
    except Exception as e:
        logger.error(f'Error fetching live blood requests: {str(e)}', exc_info=True)
        return Response(
            {'detail': 'An error occurred while fetching live blood requests.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



# ============================================================================
# NEW ENHANCED API ENDPOINTS FOR REAL-TIME TRACKING SYSTEM
# ============================================================================

from .models import RequestResponse, DonorLocationHistory
from django.db.models import Q
import math


def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points using Haversine formula"""
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


@api_view(['GET'])
@permission_classes([AllowAny])
def get_live_requests(request):
    """
    Get all active blood requests for homepage display
    Returns requests with urgency levels and basic info
    """
    try:
        # Get active, non-expired requests (more inclusive filter)
        now = timezone.now()
        
        # First, let's log what we're looking for
        total_requests = BloodRequest.objects.count()
        active_requests = BloodRequest.objects.filter(status__in=['active', 'approved', 'pending', 'partially_fulfilled']).count()
        non_expired = BloodRequest.objects.filter(expires_at__gt=now).count()
        
        logger.info(f'Total requests in DB: {total_requests}')
        logger.info(f'Active/approved/pending requests: {active_requests}')
        logger.info(f'Non-expired requests: {non_expired}')
        logger.info(f'Current time: {now}')
        
        requests = BloodRequest.objects.filter(
            status__in=['active', 'approved', 'pending', 'partially_fulfilled'],
            expires_at__gt=now
        ).order_by('-priority', '-created_at')[:20]  # Limit to 20
        
        logger.info(f'Found {requests.count()} live requests to display')
        
        # Log details of each request for debugging
        for req in requests:
            time_until_expiry = req.expires_at - now
            hours_left = time_until_expiry.total_seconds() / 3600
            logger.info(
                f'Request #{req.id}: '
                f'status={req.status}, '
                f'priority={req.priority}, '
                f'blood_group={req.patient_blood_group}, '
                f'city={req.city}, '
                f'expires_at={req.expires_at}, '
                f'hours_until_expiry={hours_left:.1f}, '
                f'required_by={req.required_by}'
            )
        
        data = []
        for req in requests:
            data.append({
                'id': req.id,
                'patient_blood_group': req.patient_blood_group,
                'hospital_name': req.hospital_name,
                'city': req.city,
                'state': req.state,
                'priority': req.priority,
                'contact_phone': req.contact_phone,
                'created_at': req.created_at.isoformat(),
                'required_units': req.required_units,
                'fulfilled_units': req.fulfilled_units,
                'latitude': float(req.latitude) if req.latitude else 0,
                'longitude': float(req.longitude) if req.longitude else 0,
            })
        
        return Response(data, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f'Error fetching live requests: {str(e)}', exc_info=True)
        return Response(
            {'error': 'Failed to load live requests'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def respond_to_request(request, request_id):
    """
    Donor responds to a blood request
    Status: interested -> en_route -> arrived -> donated
    """
    try:
        blood_request = BloodRequest.objects.get(id=request_id)
        
        # Check if request is still active
        if not blood_request.is_active:
            return Response(
                {'error': 'This request is no longer active'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if donor already responded
        existing_response = RequestResponse.objects.filter(
            request=blood_request,
            donor=request.user
        ).first()
        
        if existing_response:
            return Response(
                {'error': 'You have already responded to this request'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if max donors reached
        if not blood_request.can_accept_more_donors:
            return Response(
                {'error': 'Maximum donor limit reached for this request'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get donor location from request data or user profile
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        
        # Calculate distance if location provided
        distance_km = None
        if latitude and longitude:
            distance_km = calculate_distance(
                float(latitude), float(longitude),
                float(blood_request.latitude), float(blood_request.longitude)
            )
        
        # Create response
        response_obj = RequestResponse.objects.create(
            request=blood_request,
            donor=request.user,
            status='interested',
            donor_latitude=latitude,
            donor_longitude=longitude,
            distance_km=distance_km,
            last_location_update=timezone.now() if latitude else None
        )
        
        # Send notification to requester
        try:
            from notifications.services import NotificationService
            notification_service = NotificationService()
            notification_service.notify_user(
                blood_request.requester,
                f'New donor response!',
                f'{request.user.get_full_name()} is interested in donating blood.',
                'donor_response',
                related_object=response_obj
            )
        except Exception as notif_error:
            logger.error(f'Failed to send notification: {str(notif_error)}')
        
        serializer_data = {
            'id': response_obj.id,
            'status': response_obj.status,
            'responded_at': response_obj.responded_at.isoformat(),
            'distance_km': distance_km,
            'message': 'Successfully responded to request!'
        }
        
        return Response(serializer_data, status=status.HTTP_201_CREATED)
    
    except BloodRequest.DoesNotExist:
        return Response(
            {'error': 'Request not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f'Error responding to request: {str(e)}', exc_info=True)
        return Response(
            {'error': 'Failed to respond to request'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_request_responses(request, request_id):
    """
    Get all responses for a specific request (for requester dashboard)
    Shows interested donors with their locations
    """
    try:
        blood_request = BloodRequest.objects.get(id=request_id)
        
        # Only requester can see all responses
        if blood_request.requester != request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        responses = RequestResponse.objects.filter(
            request=blood_request
        ).select_related('donor').order_by('distance_km', '-responded_at')
        
        data = []
        for resp in responses:
            donor = resp.donor
            data.append({
                'id': resp.id,
                'donor_name': donor.get_full_name() or donor.username,
                'donor_id': donor.id,
                'blood_group': getattr(donor, 'blood_group', 'N/A'),
                'status': resp.status,
                'distance_km': float(resp.distance_km) if resp.distance_km else None,
                'estimated_arrival': resp.estimated_arrival_minutes,
                'latitude': float(resp.donor_latitude) if resp.donor_latitude else None,
                'longitude': float(resp.donor_longitude) if resp.donor_longitude else None,
                'last_update': resp.last_location_update.isoformat() if resp.last_location_update else None,
                'response_time': resp.response_time_minutes,
                'is_selected': resp.is_selected,
                'phone': donor.phone if hasattr(donor, 'phone') else None,
            })
        
        return Response({
            'request_id': blood_request.id,
            'total_responses': len(data),
            'responses': data
        }, status=status.HTTP_200_OK)
    
    except BloodRequest.DoesNotExist:
        return Response(
            {'error': 'Request not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f'Error fetching responses: {str(e)}', exc_info=True)
        return Response(
            {'error': 'Failed to load responses'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def select_donor(request, response_id):
    """
    Requester selects a donor from responses
    """
    try:
        response_obj = RequestResponse.objects.get(id=response_id)
        blood_request = response_obj.request
        
        # Only requester can select
        if blood_request.requester != request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Mark as selected
        response_obj.is_selected = True
        response_obj.selected_at = timezone.now()
        response_obj.save(update_fields=['is_selected', 'selected_at'])
        
        # Notify selected donor
        try:
            from notifications.services import NotificationService
            notification_service = NotificationService()
            notification_service.notify_user(
                response_obj.donor,
                'You have been selected! 🎉',
                f'Your donation has been selected for {blood_request.patient_name}. Please proceed to {blood_request.hospital_name}.',
                'donor_selected',
                related_object=response_obj
            )
        except Exception as notif_error:
            logger.error(f'Failed to send selection notification: {str(notif_error)}')
        
        return Response({
            'message': 'Donor selected successfully',
            'donor_name': response_obj.donor.get_full_name(),
            'request_id': blood_request.id
        }, status=status.HTTP_200_OK)
    
    except RequestResponse.DoesNotExist:
        return Response(
            {'error': 'Response not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f'Error selecting donor: {str(e)}', exc_info=True)
        return Response(
            {'error': 'Failed to select donor'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def update_donor_location(request):
    """
    Update donor's current location (for live tracking)
    Called every 5-10 seconds when donor is en route
    """
    try:
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        accuracy = request.data.get('accuracy')
        request_id = request.data.get('request_id')
        
        if not latitude or not longitude:
            return Response(
                {'error': 'Latitude and longitude are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find active response for this donor
        response_obj = RequestResponse.objects.filter(
            donor=request.user,
            request_id=request_id,
            status__in=['interested', 'en_route', 'arrived']
        ).first()
        
        if not response_obj:
            return Response(
                {'error': 'No active donation found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Update location
        response_obj.update_location(latitude, longitude)
        
        # Calculate distance to hospital
        distance_km = calculate_distance(
            float(latitude), float(longitude),
            float(response_obj.request.latitude), float(response_obj.request.longitude)
        )
        response_obj.distance_km = distance_km
        
        # Estimate arrival time (assuming average speed of 30 km/h in city)
        estimated_minutes = int((distance_km / 30) * 60) if distance_km else None
        response_obj.estimated_arrival_minutes = estimated_minutes
        response_obj.save(update_fields=['distance_km', 'estimated_arrival_minutes'])
        
        # Store in location history (for privacy/analytics)
        DonorLocationHistory.objects.create(
            donor=request.user,
            request=response_obj.request,
            latitude=latitude,
            longitude=longitude,
            accuracy_meters=accuracy
        )
        
        return Response({
            'message': 'Location updated',
            'distance_km': distance_km,
            'estimated_arrival_minutes': estimated_minutes
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f'Error updating location: {str(e)}', exc_info=True)
        return Response(
            {'error': 'Failed to update location'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def update_response_status(request, response_id):
    """
    Update response status (interested -> en_route -> arrived -> donated)
    """
    try:
        response_obj = RequestResponse.objects.get(id=response_id)
        
        # Only the donor can update their own status
        if response_obj.donor != request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_status = request.data.get('status')
        valid_statuses = ['interested', 'en_route', 'arrived', 'donated', 'unavailable']
        
        if new_status not in valid_statuses:
            return Response(
                {'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_status = response_obj.status
        response_obj.status = new_status
        
        # Update timestamps based on status
        if new_status == 'en_route':
            response_obj.en_route_at = timezone.now()
        elif new_status == 'arrived':
            response_obj.arrived_at = timezone.now()
        elif new_status == 'donated':
            response_obj.completed_at = timezone.now()
            # Update fulfilled units
            blood_request = response_obj.request
            blood_request.fulfilled_units += 1
            
            if blood_request.fulfilled_units >= blood_request.required_units:
                blood_request.status = 'fulfilled'
            else:
                blood_request.status = 'partially_fulfilled'
            
            blood_request.save(update_fields=['fulfilled_units', 'status'])
        
        response_obj.save()
        
        # Notify requester of status change
        if new_status in ['en_route', 'arrived', 'donated']:
            try:
                from notifications.services import NotificationService
                notification_service = NotificationService()
                
                status_messages = {
                    'en_route': f'{request.user.get_full_name()} is on the way to {response_obj.request.hospital_name}',
                    'arrived': f'{request.user.get_full_name()} has arrived at the hospital',
                    'donated': f'{request.user.get_full_name()} has completed the donation! ❤️'
                }
                
                notification_service.notify_user(
                    response_obj.request.requester,
                    f'Donor Update: {new_status.replace("_", " ").title()}',
                    status_messages.get(new_status, ''),
                    'donor_status_update',
                    related_object=response_obj
                )
            except Exception as notif_error:
                logger.error(f'Failed to send status notification: {str(notif_error)}')
        
        return Response({
            'message': f'Status updated to {new_status}',
            'old_status': old_status,
            'new_status': new_status
        }, status=status.HTTP_200_OK)
    
    except RequestResponse.DoesNotExist:
        return Response(
            {'error': 'Response not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f'Error updating status: {str(e)}', exc_info=True)
        return Response(
            {'error': 'Failed to update status'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_my_active_responses(request):
    """
    Get all active responses by the current user (donor dashboard)
    """
    try:
        responses = RequestResponse.objects.filter(
            donor=request.user,
            status__in=['interested', 'en_route', 'arrived']
        ).select_related('request').order_by('-responded_at')
        
        data = []
        for resp in responses:
            req = resp.request
            data.append({
                'response_id': resp.id,
                'request_id': req.id,
                'patient_name': req.patient_name,
                'blood_group': req.patient_blood_group,
                'hospital': req.hospital_name,
                'hospital_address': req.exact_address or f"{req.hospital_name}, {req.city}",
                'status': resp.status,
                'distance_km': float(resp.distance_km) if resp.distance_km else None,
                'estimated_arrival': resp.estimated_arrival_minutes,
                'hospital_latitude': float(req.latitude),
                'hospital_longitude': float(req.longitude),
                'donor_latitude': float(resp.donor_latitude) if resp.donor_latitude else None,
                'donor_longitude': float(resp.donor_longitude) if resp.donor_longitude else None,
                'is_selected': resp.is_selected,
                'contact_person': req.contact_person,
                'contact_phone': req.contact_phone,
                'responded_at': resp.responded_at.isoformat(),
            })
        
        return Response({
            'total_active': len(data),
            'responses': data
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f'Error fetching my responses: {str(e)}', exc_info=True)
        return Response(
            {'error': 'Failed to load your responses'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def verify_requests_page(request):
    """
    Admin verification page for pending blood requests
    Shows all pending requests with prescription preview and approve/reject actions
    """
    # Check if user is admin/staff
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('/accounts/login/?next=/admin/verify/')
    
    from django.db.models import Count, Q
    from datetime import timedelta
    
    # Get all pending requests
    pending_requests = BloodRequest.objects.filter(
        status='pending'
    ).order_by(
        '-priority',  # Emergency first
        'required_by'  # Then by urgency
    )
    
    # Statistics
    pending_count = pending_requests.count()
    
    today = timezone.now().date()
    approved_today = BloodRequest.objects.filter(
        status='approved',
        approved_at__date=today
    ).count()
    
    rejected_today = BloodRequest.objects.filter(
        status='cancelled',
        updated_at__date=today,
        approval_notes__icontains='rejected'
    ).count()
    
    # Average response time (mock for now - can be calculated from logs)
    avg_response_time = 15  # minutes
    
    context = {
        'pending_requests': pending_requests,
        'pending_count': pending_count,
        'approved_today': approved_today,
        'rejected_today': rejected_today,
        'avg_response_time': avg_response_time,
    }
    
    return render(request, 'admin/verify_requests.html', context)


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def verify_request_api(request, request_id):
    """
    API endpoint to approve or reject a blood request
    Triggers notifications to donors on approval
    """
    try:
        blood_request = BloodRequest.objects.get(id=request_id)
    except BloodRequest.DoesNotExist:
        return Response(
            {'error': 'Request not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    action = request.data.get('action')
    notes = request.data.get('notes', '')
    
    if action not in ['approve', 'reject']:
        return Response(
            {'error': 'Invalid action. Use "approve" or "reject"'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if action == 'approve':
        # Approve the request
        blood_request.status = 'approved'
        blood_request.approved_by = request.user
        blood_request.approved_at = timezone.now()
        blood_request.approval_notes = notes
        blood_request.activated_at = timezone.now()
        blood_request.save()
        
        # Trigger notification to matching donors (Phase 3 - Auto-Broadcast)
        try:
            from notifications.services import BloodRequestNotificationService
            notified_count = BloodRequestNotificationService.send_blood_request_notification(
                blood_request=blood_request,
                limit=50
            )
            logger.info(f"Request #{request_id} approved by {request.user.username}. Notified {notified_count} compatible donors.")
        except Exception as e:
            logger.error(f"Failed to send donor notifications for request #{request_id}: {str(e)}")
        
        return Response({
            'success': True,
            'message': f'Request approved successfully. {notified_count if "notified_count" in locals() else 0} donors notified.',
            'status': 'approved',
            'notified_donors': notified_count if 'notified_count' in locals() else 0
        }, status=status.HTTP_200_OK)
    
    elif action == 'reject':
        if not notes:
            return Response(
                {'error': 'Rejection reason is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Reject the request
        blood_request.status = 'cancelled'
        blood_request.approved_by = request.user
        blood_request.approved_at = timezone.now()
        blood_request.approval_notes = f"REJECTED: {notes}"
        blood_request.save()
        
        # Send notification to requester about rejection (Phase 3)
        try:
            from notifications.models import Notification
            Notification.objects.create(
                user=blood_request.requester,
                notification_type='request_update',
                title='❌ Blood Request Rejected',
                message=f'Your blood request for {blood_request.patient_name} has been rejected.\n\nReason: {notes}\n\nPlease correct the issues and submit a new request with valid prescription.',
                related_request=blood_request,
                priority='high'
            )
            logger.info(f"Request #{request_id} rejected by {request.user.username}. Notified requester.")
        except Exception as e:
            logger.error(f"Failed to send rejection notification for request #{request_id}: {str(e)}")
        
        return Response({
            'success': True,
            'message': 'Request rejected. Requester has been notified.',
            'status': 'cancelled'
        }, status=status.HTTP_200_OK)


def accept_request_view(request, request_id):
    """
    Phase 4: Donor accepts a blood request
    Creates chat room and redirects to tracking dashboard
    """
    from django.contrib.auth.decorators import login_required
    from django.http import HttpResponseForbidden
    
    if not request.user.is_authenticated:
        return redirect(f'/accounts/login/?next=/requests/{request_id}/accept/')
    
    try:
        blood_request = BloodRequest.objects.get(id=request_id)
    except BloodRequest.DoesNotExist:
        messages.error(request, 'Blood request not found.')
        return redirect('/')
    
    # Check if request is still active
    if blood_request.status not in ['approved', 'active', 'partially_fulfilled']:
        messages.warning(request, 'This request is no longer active.')
        return redirect('/')
    
    # Check if donor already accepted
    from .models import RequestResponse
    existing_response = RequestResponse.objects.filter(
        request=blood_request,
        donor=request.user
    ).first()
    
    if existing_response:
        messages.info(request, 'You have already responded to this request.')
        return redirect(f'/requests/track/{request_id}/')
    
    # Create response record
    RequestResponse.objects.create(
        request=blood_request,
        donor=request.user,
        status='interested',
        responded_at=timezone.now()
    )
    
    # Update request status if first donor
    if blood_request.fulfilled_units == 0:
        blood_request.status = 'matched'
        blood_request.save()
    
    # Notify requester that a donor accepted
    try:
        from notifications.models import Notification
        Notification.objects.create(
            user=blood_request.requester,
            notification_type='donor_alert',
            title=f'✅ Donor Accepted Your Request!',
            message=f'{request.user.get_full_name() or request.user.username} has accepted your blood request for {blood_request.patient_name}.\n\nYou can now chat with them to coordinate the donation.',
            related_request=blood_request,
            priority='high'
        )
    except Exception as e:
        logger.error(f"Failed to send donor acceptance notification: {str(e)}")
    
    messages.success(request, '✅ You have accepted this blood request! Redirecting to tracking dashboard...')
    return redirect(f'/requests/track/{request_id}/')
