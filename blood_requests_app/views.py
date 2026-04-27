from rest_framework import generics, permissions, filters, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import logging
import math
from accounts.decorators import check_request_eligibility, check_donation_eligibility

from .models import BloodRequest, BloodDonationCamp
from .serializers import (
    BloodRequestSerializer,
    BloodRequestCreateSerializer,
    BloodRequestDetailSerializer,
)

# Setup logging
logger = logging.getLogger(__name__)


def _get_city_coordinates(city):
    """Get approximate coordinates for major Indian cities"""
    city_coordinates = {
        'ambala': {'lat': 30.3782, 'lng': 76.7768},
        'delhi': {'lat': 28.6139, 'lng': 77.2090},
        'mumbai': {'lat': 19.0760, 'lng': 72.8777},
        'bangalore': {'lat': 12.9716, 'lng': 77.5946},
        'chennai': {'lat': 13.0827, 'lng': 80.2707},
        'kolkata': {'lat': 22.5726, 'lng': 88.3639},
        'hyderabad': {'lat': 17.3850, 'lng': 78.4867},
        'pune': {'lat': 18.5204, 'lng': 73.8567},
        'ahmedabad': {'lat': 23.0225, 'lng': 72.5714},
        'jaipur': {'lat': 26.9124, 'lng': 75.7873},
        'lucknow': {'lat': 26.8467, 'lng': 80.9462},
        'chandigarh': {'lat': 30.7333, 'lng': 76.7794},
        'haryana': {'lat': 29.0588, 'lng': 76.0856},
    }

    city_lower = city.lower().strip()
    coords = city_coordinates.get(city_lower, {'lat': 20.5937, 'lng': 78.9629})  # Default to India center
    return coords['lat'], coords['lng']


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


@check_request_eligibility
@login_required
def create_request_unified_page(request):
    """
    Blood request creation page - handles both GET and POST
    Enhanced with GPS location detection and better validation
    """

    # Handle POST request (form submission)
    if request.method == 'POST':
        try:
            logger.info('Processing blood request creation with multi-stage verification')

            # Stage 1: CAPTCHA Verification
            try:
                from captcha.helpers import captcha_unserialize
                from captcha.models import CaptchaStore
                captcha_response = request.POST.get('captcha_1')
                captcha_hashkey = request.POST.get('captcha_0')
                
                if captcha_response and captcha_hashkey:
                    try:
                        captcha = CaptchaStore.objects.get(hashkey=captcha_hashkey)
                        if not captcha.response == captcha_response:
                            from django.contrib import messages
                            messages.error(request, 'CAPTCHA verification failed. Please try again.')
                            return render(request, 'requests/create_request_unified.html', context)
                        captcha.delete()
                    except Exception as captcha_db_error:
                        logger.warning(f'CAPTCHA database error: {str(captcha_db_error)}')
                else:
                    from django.contrib import messages
                    messages.error(request, 'CAPTCHA verification required.')
                    return render(request, 'requests/create_request_unified.html', context)
            except Exception as captcha_error:
                logger.warning(f'CAPTCHA verification skipped: {str(captcha_error)}')
                # Continue without captcha if table doesn't exist
                pass

            # Extract form data
            city = request.POST.get('city', '')
            state = request.POST.get('state', '')
            hospital_address = request.POST.get('hospital_name', '')

            # Use coordinates from frontend location search if provided
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')
            
            # If coordinates not provided, fall back to server-side geocoding
            if not latitude or not longitude:
                latitude, longitude = 28.6139, 77.2090  # Default Delhi
                if city and state:
                    try:
                        import requests
                        address_query = f"{hospital_address}, {city}, {state}, India"
                        url = f"https://nominatim.openstreetmap.org/search?format=json&q={address_query}"
                        headers = {'User-Agent': 'BloodDonationApp/1.0'}

                        response = requests.get(url, headers=headers, timeout=5)
                        if response.status_code == 200:
                            geodata = response.json()
                            if geodata and len(geodata) > 0:
                                latitude = float(geodata[0]['lat'])
                                longitude = float(geodata[0]['lon'])
                                logger.info(f'Geocoded {city}, {state} to {latitude}, {longitude}')
                            else:
                                # Fallback to city coordinates
                                latitude, longitude = _get_city_coordinates(city)
                                logger.warning(f'Geocoding failed for {city}, using fallback')
                    except Exception as e:
                        logger.error(f'Geocoding error: {e}')
                        latitude, longitude = _get_city_coordinates(city)
            else:
                # Convert to float if provided as strings
                latitude = float(latitude)
                longitude = float(longitude)
                logger.info(f'Using frontend-provided coordinates: {latitude}, {longitude}')

            data = {
                'patient_name': request.POST.get('patient_name'),
                'patient_age': request.POST.get('patient_age'),
                'patient_blood_group': request.POST.get('patient_blood_group'),
                'required_units': request.POST.get('required_units'),
                'reason': request.POST.get('reason'),
                'priority': request.POST.get('priority', 'normal'),
                'required_by': request.POST.get('required_by'),
                'hospital_name': request.POST.get('hospital_name'),
                'city': city,
                'state': state,
                'pincode': request.POST.get('pincode', '110001'),
                'contact_person': request.POST.get('contact_person'),
                'contact_phone': request.POST.get('contact_phone'),
                'contact_email': request.POST.get('contact_email'),
                'requester_type': 'individual',
                'latitude': latitude,
                'longitude': longitude,
            }

            # Enhanced validation
            required_fields = ['patient_name', 'patient_age', 'patient_blood_group',
                             'required_units', 'reason', 'required_by', 'hospital_name',
                             'city', 'state', 'contact_person', 'contact_phone', 'contact_email']

            missing_fields = [f for f in required_fields if not data.get(f)]
            if missing_fields:
                logger.error(f'Missing required fields: {missing_fields}')
                from django.contrib import messages
                messages.error(request, f'Missing required fields: {", ".join(missing_fields)}')
                return render(request, 'requests/create_request_unified.html', context)

            # Validate patient age (must be between 0 and 120)
            try:
                patient_age = int(data['patient_age'])
                if patient_age < 0 or patient_age > 120:
                    messages.error(request, 'Patient age must be between 0 and 120')
                    return render(request, 'requests/create_request_unified.html', context)
            except ValueError:
                messages.error(request, 'Invalid patient age')
                return render(request, 'requests/create_request_unified.html', context)

            # Validate required units (must be between 1 and 10)
            try:
                required_units = int(data['required_units'])
                if required_units < 1 or required_units > 10:
                    messages.error(request, 'Required units must be between 1 and 10')
                    return render(request, 'requests/create_request_unified.html', context)
            except ValueError:
                messages.error(request, 'Invalid required units')
                return render(request, 'requests/create_request_unified.html', context)

            # Validate phone number
            import re
            phone = data['contact_phone']
            if not re.match(r'^\+?1?\d{9,15}$', phone):
                messages.error(request, 'Please enter a valid phone number')
                return render(request, 'requests/create_request_unified.html', context)

            # Create serializer and validate
            from .serializers import BloodRequestCreateSerializer
            serializer = BloodRequestCreateSerializer(data=data)

            if serializer.is_valid():
                # Save the request
                blood_request = serializer.save(requester=request.user)
                logger.info(f'Blood request created by user: {request.user.id}')

                # Stage 2: Multi-stage verification process - ALL requests must be verified
                priority = blood_request.priority
                
                # ALL requests go through verification first (privacy & security)
                blood_request.status = 'pending_verification'
                blood_request.verification_status = 'pending'
                blood_request.save()
                logger.info(f'Stage 2: Request {blood_request.id} requires verification before broadcasting')
                
                # Notify admins for verification
                try:
                    from django.contrib.auth import get_user_model
                    User = get_user_model()
                    admin_users = User.objects.filter(is_staff=True)
                    
                    from notifications.models import Notification
                    for admin in admin_users:
                        Notification.objects.create(
                            user=admin,
                            request=blood_request,
                            notification_type='admin_verification_required',
                            title=f'Verification Required: {priority.upper()} Blood Request',
                            message=f'New {priority} priority blood request requires your approval. Patient: {blood_request.patient_name}, Blood Group: {blood_request.patient_blood_group}, Hospital: {blood_request.hospital_name}. Once approved, it will be sent to compatible {blood_request.patient_blood_group} donors only.'
                        )
                    logger.info(f'Notified {admin_users.count()} admins for verification')
                except Exception as admin_error:
                    logger.error(f'Failed to notify admins: {str(admin_error)}')
                
                from django.contrib import messages
                if priority in ['emergency', 'high']:
                    messages.success(request, 'Blood request created successfully! It will be reviewed by admin within 30 minutes due to high priority. Once approved, it will be sent to compatible donors.')
                else:
                    messages.success(request, 'Blood request created successfully! It will be verified and activated shortly. Once approved, it will be sent to compatible donors.')

                # Stage 3: Medical certificate verification (if provided)
                medical_certificate = request.FILES.get('medical_certificate')
                if medical_certificate:
                    logger.info(f'Stage 3: Medical certificate uploaded for request {blood_request.id}')
                    # Certificate will be reviewed during admin verification

                # Stage 4: Notifications will be sent AFTER admin verification approves the request
                # No immediate notification - wait for verification approval
                logger.info(f'Stage 4: Request {blood_request.id} waiting for verification approval before broadcasting to donors')
                
                # Redirect to success
                from django.shortcuts import redirect
                return redirect('/requests/my-requests/')
            else:
                # Validation errors
                logger.error(f'Form validation errors: {serializer.errors}')
                from django.contrib import messages
                error_messages = []
                for field, errors in serializer.errors.items():
                    error_messages.append(f'{field}: {", ".join(errors)}')
                messages.error(request, f'Validation errors: {" | ".join(error_messages)}')
                return render(request, 'requests/create_request_unified.html', context)

        except Exception as e:
            logger.error(f'❌ Error processing POST request: {str(e)}', exc_info=True)
            from django.contrib import messages
            messages.error(request, f'Error creating request: {str(e)}')
            return render(request, 'requests/create_request_unified.html', context)

    # GET request - render the form with auto-filled user data
    
    # Initialize CAPTCHA form
    captcha_form = None
    try:
        from captcha.fields import CaptchaField
        from django import forms
        
        class RequestCaptchaForm(forms.Form):
            captcha = CaptchaField()
        
        captcha_form = RequestCaptchaForm()
    except Exception as captcha_error:
        logger.warning(f'CAPTCHA form not available: {str(captcha_error)}')
    
    context = {
        'user_name': request.user.get_full_name() or request.user.username,
        'user_phone': getattr(request.user, 'phone_number', '') or '',
        'user_email': request.user.email,
        'user_city': getattr(request.user, 'city', '') or '',
        'user_state': getattr(request.user, 'state', '') or '',
        'user_pincode': getattr(request.user, 'pincode', '') or '',
        'user_latitude': getattr(request.user, 'latitude', 28.6139),
        'user_longitude': getattr(request.user, 'longitude', 77.2090),
        'blood_types': ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'],
        'urgency_levels': [
            {'value': 'low', 'label': 'Low Priority', 'color': 'green', 'description': 'Within 3-5 days'},
            {'value': 'normal', 'label': 'Normal', 'color': 'blue', 'description': 'Within 24-48 hours'},
            {'value': 'high', 'label': 'High Priority', 'color': 'orange', 'description': 'Within 12-24 hours'},
            {'value': 'emergency', 'label': 'Emergency', 'color': 'red', 'description': 'Immediate - Critical'},
        ],
        'captcha_form': captcha_form,
    }
    return render(request, 'requests/create_request_unified.html', context)


def track_request_dashboard(request, request_id=None):
    """
    Enhanced unified tracking dashboard for blood requests
    Shows user's own requests with stats and live requests from other donors
    Zomato-style UI with live map, donor tracking, and real-time updates
    If request_id is provided, shows details for that specific request
    """
    if not request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect('/accounts/login/?next=/requests/track/')

    try:
        # Get user location
        user_lat = getattr(request.user, 'latitude', None)
        user_lng = getattr(request.user, 'longitude', None)

        # Get user's requests
        from .models import BloodRequest, RequestResponse
        from django.utils import timezone

        my_requests = BloodRequest.objects.filter(
            requester=request.user
        ).order_by('-created_at')

        # Categorize requests
        active_requests = my_requests.filter(status__in=['active', 'partially_fulfilled'])
        completed_requests = my_requests.filter(status='fulfilled')
        cancelled_requests = my_requests.filter(status__in=['cancelled', 'expired'])

        # Get live blood requests (for donors to see)
        live_requests = BloodRequest.objects.filter(
            status__in=['active', 'partially_fulfilled']
        ).exclude(requester=request.user).select_related('requester').order_by('-created_at')[:10]

        # Calculate distances for live requests
        requests_with_distance = []
        for req in live_requests:
            distance = None
            if user_lat and user_lng and hasattr(req, 'latitude') and hasattr(req, 'longitude'):
                distance = calculate_distance(
                    user_lat, user_lng,
                    float(req.latitude), float(req.longitude)
                )

            requests_with_distance.append({
                'request': req,
                'distance': round(distance, 1) if distance else None,
                'time_ago': get_time_ago(req.created_at)
            })

        context = {
            'my_requests': my_requests,
            'active_requests': active_requests,
            'completed_requests': completed_requests,
            'cancelled_requests': cancelled_requests,
            'live_requests': requests_with_distance,
            'user_location': {
                'lat': user_lat,
                'lng': user_lng
            },
            'blood_request': None  # Will be set if request_id is provided
        }
        
        # If request_id is provided, get that specific request
        if request_id:
            try:
                from django.shortcuts import get_object_or_404
                blood_request = get_object_or_404(BloodRequest, id=request_id)
                context['blood_request'] = blood_request
                
                # Get responses for this request
                user_response = None
                if request.user.is_authenticated:
                    user_response = RequestResponse.objects.filter(
                        request=blood_request,
                        donor=request.user
                    ).first()
                
                all_responses = RequestResponse.objects.filter(
                    request=blood_request
                ).select_related('donor').order_by('-responded_at')
                
                # Enrich donor details with distance, ETA, and status
                donor_details = []
                for response in all_responses:
                    donor = response.donor
                    distance_km = None
                    eta_minutes = None
                    
                    # Calculate distance if both locations available
                    if (hasattr(response, 'donor_latitude') and response.donor_latitude and 
                        hasattr(blood_request, 'latitude') and blood_request.latitude):
                        distance_km = calculate_distance(
                            float(response.donor_latitude), float(response.donor_longitude or 0),
                            float(blood_request.latitude), float(blood_request.longitude or 0)
                        )
                        # Estimate ETA (assuming 30 km/h average speed in city)
                        eta_minutes = int((distance_km / 30) * 60) if distance_km else None
                    
                    donor_details.append({
                        'response': response,
                        'donor': donor,
                        'name': donor.get_full_name() or donor.username,
                        'blood_group': getattr(donor, 'blood_group', 'N/A'),
                        'phone': getattr(donor, 'phone_number', 'N/A'),
                        'distance_km': round(distance_km, 1) if distance_km else None,
                        'eta_minutes': eta_minutes,
                        'response_time': response.response_time_minutes if hasattr(response, 'response_time_minutes') else None,
                        'status': response.get_status_display(),
                        'status_class': response.status,
                    })
                
                context['user_response'] = user_response
                context['all_responses'] = all_responses
                context['donor_details'] = donor_details
            except Exception as e:
                logger.warning(f'Request {request_id} not found: {str(e)}')

        return render(request, 'requests/track_request_dashboard.html', context)

    except Exception as e:
        # Fallback to basic dashboard
        logger.error(f'Error in track_request_dashboard: {str(e)}', exc_info=True)
        return render(request, 'requests/track_request_dashboard.html', {
            'my_requests': [],
            'active_requests': [],
            'completed_requests': [],
            'cancelled_requests': [],
            'live_requests': [],
            'blood_request': None
        })


def track_specific_request(request, request_id):
    """
    Track a specific blood request by ID
    Shows detailed information and allows donors to accept
    """
    from django.shortcuts import redirect, render
    from .models import BloodRequest, RequestResponse
    from django.utils import timezone

    if not request.user.is_authenticated:
        return redirect('/accounts/login/?next=/requests/track/{}/'.format(request_id))

    try:
        blood_request = BloodRequest.objects.get(id=request_id)
    except BloodRequest.DoesNotExist:
        context = {
            'error': 'Request not found',
            'request_id': request_id
        }
        return render(request, 'requests/track_request_error.html', context)

    # Check if user has already responded
    user_response = None
    if request.user.is_authenticated:
        user_response = RequestResponse.objects.filter(
            request=blood_request,
            donor=request.user
        ).first()

    # Get all responses for this request
    all_responses = RequestResponse.objects.filter(
        request=blood_request
    ).select_related('donor').order_by('-responded_at')

    context = {
        'blood_request': blood_request,
        'user_response': user_response,
        'all_responses': all_responses,
        'current_time': timezone.now(),
    }

    return render(request, 'requests/track_specific_request.html', context)


@login_required
@require_POST
def delete_request_permanently(request, request_id):
    """
    Permanently delete a blood request
    Only the requester can delete their own request
    """
    from django.http import JsonResponse
    from django.shortcuts import redirect
    from django.contrib import messages
    from .models import BloodRequest
    
    try:
        blood_request = BloodRequest.objects.get(id=request_id)
        
        # Check if user is the requester
        if blood_request.requester != request.user:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'You can only delete your own requests'
                }, status=403)
            messages.error(request, 'You can only delete your own requests')
            return redirect('requests:my-blood-requests')
        
        # Check if request is in a state that can be deleted
        if blood_request.status in ['active', 'fulfilled']:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Cannot delete request that is active or fulfilled'
                }, status=400)
            messages.error(request, 'Cannot delete request that is active or fulfilled')
            return redirect('requests:my-blood-requests')
        
        # Delete the request
        request_id_str = str(blood_request.id)
        blood_request.delete()
        
        # Check if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Request deleted permanently'
            })
        
        messages.success(request, 'Request deleted permanently')
        return redirect('requests:my-blood-requests')
        
    except BloodRequest.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'Request not found'
            }, status=404)
        messages.error(request, 'Request not found')
        return redirect('requests:my-blood-requests')
    except Exception as e:
        logger.error(f'Error deleting request: {str(e)}', exc_info=True)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'An error occurred while deleting the request'
            }, status=500)
        messages.error(request, 'An error occurred while deleting the request')
        return redirect('requests:my-blood-requests')


def manage_request(request, request_id):
    """
    Manage individual blood request (cancel, update, etc.)
    """
    if not request.user.is_authenticated:
        return redirect('/accounts/login/?next=/requests/manage/{}/'.format(request_id))

    from .models import BloodRequest

    try:
        blood_request = BloodRequest.objects.get(id=request_id, requester=request.user)
    except BloodRequest.DoesNotExist:
        messages.error(request, 'Request not found or you do not have permission to manage it.')
        return redirect('/requests/track/')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'cancel':
            # Cancel the request
            if blood_request.status in ['pending', 'active']:
                blood_request.status = 'cancelled'
                blood_request.save()
                messages.success(request, 'Request cancelled successfully.')
            else:
                messages.error(request, 'Cannot cancel a request that is already completed or cancelled.')

        elif action == 'update_urgency':
            # Update urgency/priority
            new_priority = request.POST.get('priority')
            if new_priority in ['low', 'normal', 'high', 'emergency']:
                blood_request.priority = new_priority
                blood_request.save()
                messages.success(request, 'Request priority updated successfully.')
            else:
                messages.error(request, 'Invalid priority level.')

        elif action == 'update_required_by':
            # Update required by date
            new_date = request.POST.get('required_by')
            if new_date:
                from datetime import datetime
                try:
                    blood_request.required_by = datetime.strptime(new_date, '%Y-%m-%d').date()
                    blood_request.save()
                    messages.success(request, 'Required date updated successfully.')
                except ValueError:
                    messages.error(request, 'Invalid date format.')
        
        elif action == 'complete':
            # Mark request as fulfilled and delete from database
            if blood_request.status not in ['fulfilled', 'cancelled']:
                # Send final notifications to all participating donors
                try:
                    from notifications.models import Notification
                    from .models import RequestResponse
                    
                    participating_donors = RequestResponse.objects.filter(
                        request=blood_request,
                        status__in=['donated', 'en_route', 'arrived']
                    ).select_related('donor')
                    
                    for response in participating_donors:
                        Notification.objects.create(
                            user=response.donor,
                            notification_type='request_completed',
                            title='✅ Blood Request Completed',
                            message=f'The blood request for {blood_request.patient_name} has been completed. Thank you for your contribution!',
                            related_request=blood_request,
                            priority='medium'
                        )
                except Exception as notif_error:
                    logger.error(f'Failed to send completion notifications: {str(notif_error)}')
                
                # Delete the request from database
                request_id_to_log = blood_request.id
                blood_request.delete()
                
                messages.success(request, 'Request marked as complete and removed from the system. All participating donors have been notified.')
                logger.info(f'Request #{request_id_to_log} completed and deleted by user {request.user.id}')
                
                # Redirect to track request dashboard
                return redirect('requests:track-request-dashboard')
            else:
                messages.error(request, 'Cannot complete a request that is already fulfilled or cancelled.')

        return redirect('requests:track-request-dashboard')

    context = {
        'request': blood_request,
    }
    return render(request, 'requests/manage_request.html', context)


@login_required
def bulk_delete_requests(request):
    """
    Delete multiple blood requests at once
    Only allows deletion of user's own requests
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        import json
        data = json.loads(request.body)
        request_ids = data.get('request_ids', [])
        
        if not request_ids:
            return JsonResponse({'error': 'No request IDs provided'}, status=400)
        
        # Only delete user's own requests
        user_requests = BloodRequest.objects.filter(
            id__in=request_ids,
            requester=request.user
        )
        
        deleted_count = user_requests.count()
        
        # Send notifications to participating donors before deletion
        try:
            from notifications.models import Notification
            from .models import RequestResponse
            
            for blood_request in user_requests:
                participating_donors = RequestResponse.objects.filter(
                    request=blood_request,
                    status__in=['donated', 'en_route', 'arrived']
                ).select_related('donor')
                
                for response in participating_donors:
                    Notification.objects.create(
                        user=response.donor,
                        notification_type='request_deleted',
                        title='🗑️ Blood Request Removed',
                        message=f'The blood request for {blood_request.patient_name} has been removed from the system.',
                        related_request=blood_request,
                        priority='low'
                    )
        except Exception as notif_error:
            logger.error(f'Failed to send deletion notifications: {str(notif_error)}')
        
        # Delete all requests
        user_requests.delete()
        
        logger.info(f'Bulk deleted {deleted_count} requests by user {request.user.id}')
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully deleted {deleted_count} request(s)',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        logger.error(f'Error in bulk delete: {str(e)}', exc_info=True)
        return JsonResponse({'error': 'Failed to delete requests'}, status=500)


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

            # Geocoding: Convert address to latitude/longitude
            city = serializer.validated_data.get('city', '')
            state = serializer.validated_data.get('state', '')
            hospital_address = serializer.validated_data.get('hospital_address', '')

            if city and state:
                try:
                    import requests
                    # Use Nominatim (OpenStreetMap) for free geocoding
                    address_query = f"{hospital_address}, {city}, {state}, India"
                    url = f"https://nominatim.openstreetmap.org/search?format=json&q={address_query}"
                    headers = {'User-Agent': 'BloodDonationApp/1.0'}

                    response = requests.get(url, headers=headers, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        if data and len(data) > 0:
                            serializer.validated_data['latitude'] = float(data[0]['lat'])
                            serializer.validated_data['longitude'] = float(data[0]['lon'])
                            logger.info(f'Geocoded {city}, {state} to {data[0]["lat"]}, {data[0]["lon"]}')
                        else:
                            # Fallback to approximate city coordinates
                            logger.warning(f'Geocoding failed for {city}, {state}, using fallback')
                            lat, lng = _get_city_coordinates(city)
                            serializer.validated_data['latitude'] = lat
                            serializer.validated_data['longitude'] = lng
                    else:
                        logger.warning(f'Geocoding API error: {response.status_code}')
                        lat, lng = _get_city_coordinates(city)
                        serializer.validated_data['latitude'] = lat
                        serializer.validated_data['longitude'] = lng
                except Exception as e:
                    logger.error(f'Geocoding error: {e}')
                    lat, lng = _get_city_coordinates(city)
                    serializer.validated_data['latitude'] = lat
                    serializer.validated_data['longitude'] = lng
            else:
                # Set fallback if no city/state provided
                lat, lng = _get_city_coordinates(city or 'Unknown')
                serializer.validated_data['latitude'] = lat
                serializer.validated_data['longitude'] = lng

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
                    logger.error(f'Failed to send notifications: {str(notif_error)}', exc_info=True)
                    # Continue even if notification fails - don't crash the request
        except Exception as e:
            logger.error(f'Error in perform_create: {str(e)}', exc_info=True)
            raise


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
    Filters by blood group compatibility - only shows requests the user can donate to.
    Ordered by urgency and creation time.
    """
    try:
        # Debug: Check total requests in database
        total_requests = BloodRequest.objects.count()
        logger.info(f'Total blood requests in database: {total_requests}')

        # TEMPORARY: Return dummy data for testing if no requests in DB
        if total_requests == 0:
            logger.warning('No requests in database, returning dummy data for testing')
            dummy_data = [
                {
                    'id': 999,
                    'patient_blood_group': 'A+',
                    'hospital_name': 'City Hospital',
                    'city': 'Delhi',
                    'state': 'Delhi',
                    'priority': 'emergency',
                    'status': 'active',
                    'created_at': timezone.now().isoformat(),
                    'latitude': 28.6139,
                    'longitude': 77.2090
                },
                {
                    'id': 998,
                    'patient_blood_group': 'O+',
                    'hospital_name': 'Apollo Hospital',
                    'city': 'Mumbai',
                    'state': 'Maharashtra',
                    'priority': 'urgent',
                    'status': 'active',
                    'created_at': timezone.now().isoformat(),
                    'latitude': 19.0760,
                    'longitude': 72.8777
                },
                {
                    'id': 997,
                    'patient_blood_group': 'B+',
                    'hospital_name': 'Fortis Hospital',
                    'city': 'Bangalore',
                    'state': 'Karnataka',
                    'priority': 'normal',
                    'status': 'pending',
                    'created_at': timezone.now().isoformat(),
                    'latitude': 12.9716,
                    'longitude': 77.5946
                }
            ]
            return JsonResponse(dummy_data, safe=False)
        
        # Blood group compatibility chart (who can donate to whom)
        BLOOD_COMPATIBILITY = {
            'A+': ['A+', 'AB+'],
            'A-': ['A+', 'A-', 'AB+', 'AB-'],
            'B+': ['B+', 'AB+'],
            'B-': ['B+', 'B-', 'AB+', 'AB-'],
            'AB+': ['AB+'],
            'AB-': ['AB+', 'AB-'],
            'O+': ['O+', 'A+', 'B+', 'AB+'],
            'O-': ['O+', 'O-', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-'],  # Universal donor
        }
        
        # Get active requests
        queryset = BloodRequest.objects.filter(
            status__in=['active', 'approved', 'pending', 'partially_fulfilled', 'fulfilled', 'cancelled']
        )
        
        # PRIVACY: Exclude current user's own requests
        if request.user.is_authenticated:
            queryset = queryset.exclude(requester=request.user)
            logger.info(f'Excluding user {request.user.id}\'s requests from homepage')
            
            # FILTER BY BLOOD GROUP COMPATIBILITY
            user_blood_group = request.user.blood_group
            if user_blood_group:
                # Get blood groups this user can donate to
                compatible_patient_groups = BLOOD_COMPATIBILITY.get(user_blood_group, [])
                if compatible_patient_groups:
                    queryset = queryset.filter(patient_blood_group__in=compatible_patient_groups)
                    logger.info(f'Filtering requests for {user_blood_group} donor - showing requests for: {compatible_patient_groups}')
                else:
                    # If user has invalid blood group, return no requests
                    logger.warning(f'User {request.user.id} has invalid blood group: {user_blood_group}')
                    return Response([])
        
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
                
                # Also apply blood group filter in fallback
                user_blood_group = request.user.blood_group
                if user_blood_group:
                    compatible_patient_groups = BLOOD_COMPATIBILITY.get(user_blood_group, [])
                    if compatible_patient_groups:
                        queryset = queryset.filter(patient_blood_group__in=compatible_patient_groups)
            
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


def get_time_ago(created_at):
    """Get human-readable time ago string"""
    now = timezone.now()
    diff = now - created_at

    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} min ago"
    else:
        return "Just now"


@api_view(['GET'])
@permission_classes([AllowAny])
def get_live_requests(request):
    """
    Get all active blood requests for homepage display
    Returns requests with urgency levels and basic info
    """
    try:
        # Get active requests - remove expiry filter for debugging
        # Show ALL requests regardless of expiry
        now = timezone.now()

        # First, let's log what we're looking for
        total_requests = BloodRequest.objects.count()
        active_requests = BloodRequest.objects.filter(status__in=['active', 'approved', 'pending', 'partially_fulfilled']).count()

        logger.info(f'Total requests in DB: {total_requests}')
        logger.info(f'Active/approved/pending requests: {active_requests}')
        logger.info(f'Current time: {now}')

        requests = BloodRequest.objects.filter(
            status__in=['active', 'approved', 'pending', 'partially_fulfilled', 'fulfilled', 'cancelled']
        ).order_by('-priority', '-created_at')[:20]  # Limit to 20
        
        logger.info(f'Found {requests.count()} live requests to display')

        # Log details of each request for debugging
        for req in requests:
            logger.info(
                f'Request #{req.id}: '
                f'status={req.status}, '
                f'priority={req.priority}, '
                f'blood_group={req.patient_blood_group}, '
                f'city={req.city}, '
                f'required_by={req.required_by}'
            )
        
        data = []
        for req in requests:
            data.append({
                'id': req.id,
                'patient_blood_group': req.patient_blood_group,
                'patient_name': req.patient_name,
                'hospital_name': req.hospital_name,
                'city': req.city,
                'state': req.state,
                'priority': req.priority,
                'status': req.status,
                'contact_phone': req.contact_phone,
                'contact_person': req.contact_person,
                'created_at': req.created_at.isoformat(),
                'required_by': req.required_by.isoformat() if req.required_by else None,
                'expires_at': req.expires_at.isoformat() if req.expires_at else None,
                'required_units': req.required_units,
                'fulfilled_units': req.fulfilled_units,
                'reason': req.reason,
                'is_critical': req.is_critical,
                'is_owner': request.user.is_authenticated and req.requester == request.user,
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
@check_donation_eligibility
def respond_to_request(request, request_id):
    """
    Donor responds to a blood request (accept/reject)
    """
    from django.http import JsonResponse
    import json

    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Please login first'}, status=401)

    try:
        blood_request = BloodRequest.objects.get(id=request_id)
        logger.info(f"User {request.user.username} responding to request {request_id}")

        # Check if request is still active
        if blood_request.status in ['cancelled', 'fulfilled', 'expired']:
            return JsonResponse({'success': False, 'message': 'This request is no longer active'})

        # Check if donor already responded
        existing_response = RequestResponse.objects.filter(
            request=blood_request,
            donor=request.user
        ).first()

        if existing_response:
            return JsonResponse({'success': False, 'message': 'You have already responded to this request'})

        # Parse request body
        try:
            data = json.loads(request.body)
            action = data.get('action', 'accept')
        except Exception as e:
            logger.error(f"Error parsing request body: {e}")
            action = 'accept'

        if action == 'reject':
            return JsonResponse({'success': True, 'message': 'Request declined'})

        # Check if max donors reached
        try:
            if not blood_request.can_accept_more_donors:
                return JsonResponse({'success': False, 'message': 'Maximum donor limit reached'})
        except Exception as e:
            logger.error(f"Error checking max donors: {e}")
            # Continue anyway if this check fails

        # Get donor location from request data or user profile
        try:
            latitude = data.get('latitude', getattr(request.user, 'latitude', None))
            longitude = data.get('longitude', getattr(request.user, 'longitude', None))
        except Exception as e:
            logger.error(f"Error getting location: {e}")
            latitude = None
            longitude = None

        # Calculate distance if location provided
        distance_km = None
        try:
            if latitude and longitude and blood_request.latitude and blood_request.longitude:
                distance_km = calculate_distance(
                    float(latitude), float(longitude),
                    float(blood_request.latitude), float(blood_request.longitude)
                )
        except Exception as e:
            logger.error(f"Error calculating distance: {e}")
            distance_km = None

        # Create response
        try:
            response_obj = RequestResponse.objects.create(
                request=blood_request,
                donor=request.user,
                status='interested',
                donor_latitude=latitude,
                donor_longitude=longitude,
                distance_km=distance_km,
                last_location_update=timezone.now() if latitude else None
            )
            logger.info(f"Created response {response_obj.id} for request {request_id}")
        except Exception as e:
            logger.error(f"Error creating response: {e}")
            return JsonResponse({'success': False, 'message': f'Failed to create response: {str(e)}'}, status=500)

        # Create or get chat room for this request
        try:
            from .models_chat import ChatRoom, ChatMessage
            chat_room, created = ChatRoom.objects.get_or_create(
                blood_request=blood_request,
                room_type='request',
                defaults={
                    'name': f"Request #{blood_request.id} - {blood_request.patient_name}",
                    'is_active': True
                }
            )
            
            # Add both requester and donor to the chat room
            if created or not chat_room.participants.filter(id=blood_request.requester.id).exists():
                chat_room.participants.add(blood_request.requester)
            if not chat_room.participants.filter(id=request.user.id).exists():
                chat_room.participants.add(request.user)
            
            # Send system message to chat
            ChatMessage.objects.create(
                sender=blood_request.requester,
                receiver=request.user,
                message=f"🩸 {request.user.get_full_name() or request.user.username} has accepted your blood request for {blood_request.patient_name} ({blood_request.patient_blood_group}). You can now chat to coordinate the donation.",
                message_type='system',
                request=blood_request
            )
            
            logger.info(f"Chat room {chat_room.id} created/retrieved for request {request_id}")
        except Exception as chat_error:
            logger.error(f"Error creating chat room: {chat_error}")
            # Don't fail the request if chat room creation fails

        # Send notification to requester
        try:
            from notifications.services import NotificationService
            notification_service = NotificationService()
            notification_service.notify_user(
                blood_request.requester,
                'New donor response!',
                f'{request.user.get_full_name() or request.user.username} is interested in donating blood.',
                'donor_response',
                related_object=response_obj
            )
        except Exception as notif_error:
            logger.error(f'Failed to send notification: {str(notif_error)}')

        return JsonResponse({
            'success': True,
            'message': 'Successfully accepted request!',
            'response_id': response_obj.id,
            'distance_km': distance_km
        })
    
    except BloodRequest.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Request not found'}, status=404)
    except Exception as e:
        logger.error(f'Error in respond_to_request: {e}')
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_donor_location(request, response_id):
    """
    Get the current location of a donor for live tracking
    """
    try:
        response_obj = RequestResponse.objects.get(id=response_id)

        # Check if user has permission to view this location
        if request.user != response_obj.request.requester and request.user != response_obj.donor:
            return JsonResponse({'error': 'Permission denied'}, status=403)

        data = {
            'latitude': float(response_obj.donor_latitude) if response_obj.donor_latitude else None,
            'longitude': float(response_obj.donor_longitude) if response_obj.donor_longitude else None,
            'status': response_obj.status,
            'last_updated': response_obj.last_location_update.isoformat() if response_obj.last_location_update else None,
            'distance_km': float(response_obj.distance_km) if response_obj.distance_km else None,
        }

        return JsonResponse(data)
    except RequestResponse.DoesNotExist:
        return JsonResponse({'error': 'Response not found'}, status=404)
    except Exception as e:
        logger.error(f'Error getting donor location: {e}')
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
@login_required
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
                {'error': 'Only the requester can view responses to their blood request'},
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
            'donor_id': response_obj.donor.id,
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


@login_required
def verify_requests_page(request):
    """
    Admin verification page for pending blood requests
    Shows all pending requests with prescription preview and approve/reject actions
    """
    # Check if user is admin/staff
    if not request.user.is_staff:
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


@login_required
def admin_camps_page(request):
    """
    Admin page to manage blood donation camps
    """
    if not request.user.is_staff:
        return redirect('/accounts/login/?next=/admin/camps/')

    camps = BloodDonationCamp.objects.all().order_by('-start_date')

    context = {
        'camps': camps,
        'total_camps': camps.count(),
        'active_camps': camps.filter(status='ongoing').count(),
        'upcoming_camps': camps.filter(status='upcoming').count(),
    }

    return render(request, 'admin/camps.html', context)


@login_required
def campaign_list(request):
    """
    User-facing page to browse blood donation campaigns
    """
    from django.utils import timezone
    
    # Show active and upcoming campaigns
    campaigns = BloodDonationCamp.objects.filter(
        status__in=['ongoing', 'upcoming']
    ).order_by('-start_date')
    
    context = {
        'campaigns': campaigns,
    }
    
    return render(request, 'campaigns/list.html', context)


@login_required
def campaign_create(request):
    """
    Hospital/admin page to create a new blood donation campaign
    """
    if not (request.user.is_staff or request.user.user_type == 'hospital'):
        messages.error(request, 'You do not have permission to create campaigns.')
        return redirect('requests:campaign-list')
    
    if request.method == 'POST':
        try:
            camp = BloodDonationCamp.objects.create(
                name=request.POST.get('name'),
                description=request.POST.get('description', ''),
                venue=request.POST.get('venue'),
                address=request.POST.get('address'),
                city=request.POST.get('city'),
                state=request.POST.get('state'),
                start_date=request.POST.get('start_date'),
                end_date=request.POST.get('end_date'),
                target_units=request.POST.get('target_units', 100),
                contact_number=request.POST.get('contact_number'),
                contact_email=request.POST.get('contact_email'),
                organizer=request.user,
                status='upcoming',
                show_as_popup=request.POST.get('show_as_popup') == 'on'
            )
            
            # Handle banner image upload
            if 'banner_image' in request.FILES:
                camp.banner_image = request.FILES['banner_image']
                camp.save()
            
            messages.success(request, f'Campaign "{camp.name}" created successfully!')
            return redirect('requests:campaign-list')
        except Exception as e:
            messages.error(request, f'Error creating campaign: {str(e)}')
    
    return render(request, 'campaigns/create.html')


@login_required
def campaign_join(request, campaign_id):
    """
    User page to join a blood donation campaign
    """
    from django.shortcuts import get_object_or_404
    
    campaign = get_object_or_404(BloodDonationCamp, id=campaign_id)
    
    if campaign.status not in ['ongoing', 'upcoming']:
        messages.error(request, 'This campaign is not accepting registrations.')
        return redirect('requests:campaign-list')
    
    # For now, just show a success message
    # In a full implementation, you'd create a CampaignParticipant model
    messages.success(request, f'You have registered for "{campaign.name}". Contact: {campaign.contact_number}')
    return redirect('requests:campaign-list')


@login_required
def admin_create_camp(request):
    """
    Admin page to create a new blood donation camp
    """
    if not request.user.is_staff:
        return redirect('/accounts/login/?next=/admin/camps/create/')

    if request.method == 'POST':
        try:
            camp = BloodDonationCamp.objects.create(
                name=request.POST.get('name'),
                description=request.POST.get('description', ''),
                venue=request.POST.get('venue'),
                address=request.POST.get('address'),
                city=request.POST.get('city'),
                state=request.POST.get('state'),
                start_date=request.POST.get('start_date'),
                end_date=request.POST.get('end_date'),
                status=request.POST.get('status', 'upcoming'),
                target_units=int(request.POST.get('target_units', 100)),
                organizer=request.user,
                contact_number=request.POST.get('contact_number'),
                contact_email=request.POST.get('contact_email'),
            )
            messages.success(request, f'Blood donation camp "{camp.name}" created successfully!')
            return redirect('admin-camps-page')
        except Exception as e:
            messages.error(request, f'Error creating camp: {str(e)}')

    return render(request, 'admin/create_camp.html')


@login_required
def admin_edit_camp(request, camp_id):
    """
    Admin page to edit an existing blood donation camp
    """
    if not request.user.is_staff:
        return redirect('/accounts/login/?next=/admin/camps/')

    camp = get_object_or_404(BloodDonationCamp, id=camp_id)

    if request.method == 'POST':
        try:
            camp.name = request.POST.get('name', camp.name)
            camp.description = request.POST.get('description', camp.description)
            camp.venue = request.POST.get('venue', camp.venue)
            camp.address = request.POST.get('address', camp.address)
            camp.city = request.POST.get('city', camp.city)
            camp.state = request.POST.get('state', camp.state)
            camp.start_date = request.POST.get('start_date', camp.start_date)
            camp.end_date = request.POST.get('end_date', camp.end_date)
            camp.status = request.POST.get('status', camp.status)
            camp.target_units = int(request.POST.get('target_units', camp.target_units))
            camp.collected_units = int(request.POST.get('collected_units', camp.collected_units))
            camp.contact_number = request.POST.get('contact_number', camp.contact_number)
            camp.contact_email = request.POST.get('contact_email', camp.contact_email)
            camp.save()
            messages.success(request, f'Blood donation camp "{camp.name}" updated successfully!')
            return redirect('admin-camps-page')
        except Exception as e:
            messages.error(request, f'Error updating camp: {str(e)}')

    context = {'camp': camp}
    return render(request, 'admin/edit_camp.html', context)


@login_required
def admin_delete_camp(request, camp_id):
    """
    Admin page to delete a blood donation camp
    """
    if not request.user.is_staff:
        return redirect('/accounts/login/?next=/admin/camps/')

    camp = get_object_or_404(BloodDonationCamp, id=camp_id)

    if request.method == 'POST':
        camp_name = camp.name
        camp.delete()
        messages.success(request, f'Blood donation camp "{camp_name}" deleted successfully!')
        return redirect('admin-camps-page')

    context = {'camp': camp}
    return render(request, 'admin/delete_camp.html', context)


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


# ============================================================================
# CHAT SYSTEM (Instagram-style Direct Messaging)
# ============================================================================

from django.db.models import Q, Max, Count
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
# Import ChatMessage from models_chat (user-to-user chat, not request-specific)
from .models_chat import ChatMessage

def get_unread_chat_count(user):
    """Get unread chat message count for user"""
    return ChatMessage.objects.filter(receiver=user, is_read=False).count()


@csrf_exempt
def unread_chat_count_api(request):
    """API endpoint to get unread chat count for navbar badge"""
    try:
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': True,
                'unread_count': 0,
            })
        
        unread_count = get_unread_chat_count(request.user)
        
        return JsonResponse({
            'success': True,
            'unread_count': unread_count,
        })
    except Exception as e:
        logger.error(f'Error getting unread chat count: {str(e)}', exc_info=True)
        return JsonResponse({'error': 'Failed to get unread count'}, status=500)


@login_required
def chat_inbox(request):
    """Show all conversations (like Instagram inbox)"""
    # Get all users current user has chatted with
    sent_messages = ChatMessage.objects.filter(sender=request.user).values('receiver')
    received_messages = ChatMessage.objects.filter(receiver=request.user).values('sender')
    
    # Combine and get unique user IDs
    all_conversations = set()
    for msg in sent_messages:
        all_conversations.add(msg['receiver'])
    for msg in received_messages:
        all_conversations.add(msg['sender'])
    
    # Build conversation list with details
    conversations = []
    from accounts.models import User
    
    for user_id in all_conversations:
        try:
            other_user = User.objects.get(id=user_id, is_active=True)
            
            # Get last message
            last_message = ChatMessage.objects.filter(
                Q(sender=request.user, receiver=other_user) |
                Q(sender=other_user, receiver=request.user)
            ).order_by('-created_at').first()
            
            # Get unread count
            unread_count = ChatMessage.objects.filter(
                sender=other_user, receiver=request.user, is_read=False
            ).count()
            
            conversations.append({
                'user': other_user,
                'last_message': last_message,
                'unread_count': unread_count,
            })
        except User.DoesNotExist:
            continue
    
    # Sort by last message time
    conversations.sort(
        key=lambda x: x['last_message'].created_at if x['last_message'] else timezone.now(),
        reverse=True
    )
    
    context = {
        'conversations': conversations,
        'total_unread': sum(c['unread_count'] for c in conversations),
    }
    
    return render(request, 'chat/inbox.html', context)


@login_required
def chat_conversation(request, user_id):
    """Chat with specific user"""
    from accounts.models import User
    from accounts.models import PrivacySettings
    
    other_user = get_object_or_404(User, id=user_id, is_active=True)
    
    # Check if other user allows chat requests
    try:
        privacy_settings = other_user.privacy_settings
        if not privacy_settings.enable_chat_requests and not request.user.is_staff:
            messages.error(request, 'This user does not accept chat requests')
            return redirect('chat-inbox')
    except PrivacySettings.DoesNotExist:
        pass  # Allow by default if no settings
    
    # Get messages between users
    messages_list = ChatMessage.objects.filter(
        Q(sender=request.user, receiver=other_user) |
        Q(sender=other_user, receiver=request.user)
    ).order_by('created_at')
    
    # Mark received messages as read
    ChatMessage.objects.filter(
        sender=other_user, receiver=request.user, is_read=False
    ).update(is_read=True)
    
    context = {
        'other_user': other_user,
        'messages': messages_list,
    }
    
    return render(request, 'chat/conversation.html', context)


@login_required
def start_chat_with_donor(request, donor_id):
    """Start chat with a donor from donor search profile"""
    from accounts.models import User
    
    donor = get_object_or_404(User, id=donor_id, is_active=True)
    
    # Redirect to the existing chat conversation view
    return redirect('chat-conversation', user_id=donor_id)


@login_required
def send_chat_message(request):
    """Send chat message (AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    
    try:
        from accounts.models import User
        from accounts.models import PrivacySettings
        from notifications.models import Notification
        
        receiver_id = request.POST.get('receiver_id')
        message_text = request.POST.get('message', '').strip()
        
        if not receiver_id or not message_text:
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        receiver = get_object_or_404(User, id=receiver_id, is_active=True)
        
        # Check if receiver allows chat requests
        try:
            privacy = receiver.privacy_settings
            if not privacy.enable_chat_requests and not request.user.is_staff:
                return JsonResponse({'error': 'User does not accept chat requests'}, status=403)
        except PrivacySettings.DoesNotExist:
            pass  # Allow by default
        
        # Create message
        message = ChatMessage.objects.create(
            sender=request.user,
            receiver=receiver,
            message=message_text
        )
        
        # Create notification for receiver
        try:
            Notification.objects.create(
                user=receiver,
                notification_type='chat_message',
                title=f'New message from {request.user.first_name or request.user.username}',
                message=message_text[:100],
                priority='medium'
            )
        except Exception as e:
            logger.error(f'Error creating chat notification: {str(e)}')
        
        return JsonResponse({
            'success': True,
            'message_id': message.id,
            'created_at': message.created_at.isoformat(),
        })
        
    except Exception as e:
        logger.error(f'Error sending chat message: {str(e)}', exc_info=True)
        return JsonResponse({'error': 'Failed to send message'}, status=500)


@login_required
def mark_messages_read(request):
    """Mark messages as read (AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    
    try:
        from accounts.models import User
        
        sender_id = request.POST.get('sender_id')
        sender = get_object_or_404(User, id=sender_id)
        
        # Mark messages as read
        count = ChatMessage.objects.filter(
            sender=sender, receiver=request.user, is_read=False
        ).update(is_read=True)
        
        return JsonResponse({
            'success': True,
            'marked_read': count,
        })
        
    except Exception as e:
        logger.error(f'Error marking messages read: {str(e)}', exc_info=True)
        return JsonResponse({'error': 'Failed to mark messages as read'}, status=500)


# ============================================================================
# BLOOD REQUEST WORKFLOW APIs (Complete 20-step process)
# ============================================================================

from .services import BloodRequestWorkflow

@login_required
def activate_request_api(request, request_id):
    """Activate blood request and notify matching donors (Steps 1-6)"""
    try:
        blood_request = get_object_or_404(BloodRequest, id=request_id)
        
        # Check permission
        if blood_request.requester != request.user and not request.user.is_staff:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        # Activate request
        blood_request = BloodRequestWorkflow.activate_request(blood_request)
        
        return JsonResponse({
            'success': True,
            'message': 'Request activated and donors notified',
            'request_id': blood_request.id,
            'status': blood_request.status,
        })
    except Exception as e:
        logger.error(f'Error activating request: {str(e)}', exc_info=True)
        return JsonResponse({'error': 'Failed to activate request'}, status=500)


@login_required
def accept_request_api(request, request_id):
    """Donor accepts blood request (Steps 7-10)"""
    try:
        blood_request = get_object_or_404(BloodRequest, id=request_id, status='active')
        
        # Accept request
        response, message = BloodRequestWorkflow.donor_accept_request(
            blood_request, request.user
        )
        
        if response:
            return JsonResponse({
                'success': True,
                'message': message,
                'response_id': response.id,
                'status': response.status,
            })
        else:
            return JsonResponse({'error': message}, status=400)
            
    except Exception as e:
        logger.error(f'Error accepting request: {str(e)}', exc_info=True)
        return JsonResponse({'error': 'Failed to accept request'}, status=500)


@login_required
def decline_request_api(request, request_id):
    """Donor declines blood request"""
    try:
        blood_request = get_object_or_404(BloodRequest, id=request_id)
        
        BloodRequestWorkflow.donor_decline_request(blood_request, request.user)
        
        return JsonResponse({
            'success': True,
            'message': 'Request declined',
        })
    except Exception as e:
        logger.error(f'Error declining request: {str(e)}', exc_info=True)
        return JsonResponse({'error': 'Failed to decline request'}, status=500)


@login_required
def update_donor_status_api(request, response_id):
    """Update donor response status (Steps 13-14)"""
    try:
        from .models import RequestResponse
        
        response = get_object_or_404(RequestResponse, id=response_id)
        
        # Check permission
        if response.donor != request.user:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        new_status = request.POST.get('status')
        if not new_status:
            return JsonResponse({'error': 'Status required'}, status=400)
        
        success, message = BloodRequestWorkflow.update_donor_status(response, new_status)
        
        if success:
            return JsonResponse({
                'success': True,
                'message': message,
                'status': new_status,
            })
        else:
            return JsonResponse({'error': message}, status=400)
            
    except Exception as e:
        logger.error(f'Error updating donor status: {str(e)}', exc_info=True)
        return JsonResponse({'error': 'Failed to update status'}, status=500)


@login_required
def get_contact_details_api(request, response_id):
    """Share contact details between requester and donor (Step 11)"""
    try:
        from .models import RequestResponse
        
        response = get_object_or_404(RequestResponse, id=response_id)
        
        contact_info, message = BloodRequestWorkflow.get_donor_contact(
            response, request.user
        )
        
        if contact_info:
            return JsonResponse({
                'success': True,
                'contact': contact_info,
                'message': message,
            })
        else:
            return JsonResponse({'error': message}, status=403)
            
    except Exception as e:
        logger.error(f'Error getting contact details: {str(e)}', exc_info=True)
        return JsonResponse({'error': 'Failed to get contact details'}, status=500)


@login_required
def cancel_request_api(request, request_id):
    """Cancel blood request (Step 17)"""
    try:
        blood_request = get_object_or_404(BloodRequest, id=request_id)
        
        reason = request.POST.get('reason', 'No longer needed')
        
        success, message = BloodRequestWorkflow.cancel_request(
            blood_request, request.user, reason
        )
        
        if success:
            return JsonResponse({
                'success': True,
                'message': message,
            })
        else:
            return JsonResponse({'error': message}, status=403)
            
    except Exception as e:
        logger.error(f'Error cancelling request: {str(e)}', exc_info=True)
        return JsonResponse({'error': 'Failed to cancel request'}, status=500)


@login_required
def get_request_history_api(request, request_id):
    """Get complete request history (Step 18)"""
    try:
        blood_request = get_object_or_404(BloodRequest, id=request_id)
        
        # Check permission
        if blood_request.requester != request.user and not request.user.is_staff:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        history = BloodRequestWorkflow.get_request_history(blood_request)
        
        # Serialize response data
        responses_data = []
        for response in history['responses']:
            responses_data.append({
                'id': response.id,
                'donor_name': response.donor.get_full_name() or response.donor.username,
                'donor_blood_group': response.donor.blood_group,
                'status': response.status,
                'responded_at': response.responded_at.isoformat(),
                'distance_km': float(response.distance_km) if response.distance_km else None,
            })
        
        return JsonResponse({
            'success': True,
            'request': {
                'id': history['request'].id,
                'patient_name': history['request'].patient_name,
                'status': history['request'].status,
                'created_at': history['request'].created_at.isoformat(),
            },
            'status_history': history['status_history'],
            'responses': responses_data,
            'total_responses': history['total_responses'],
            'accepted_responses': history['accepted_responses'],
            'completed_donations': history['completed_donations'],
        })
    except Exception as e:
        logger.error(f'Error getting request history: {str(e)}', exc_info=True)
        return JsonResponse({'error': 'Failed to get request history'}, status=500)


@login_required
def update_donor_location_api(request):
    """Update donor location for live tracking"""
    try:
        from .models import RequestResponse, DonorLocationHistory
        
        response_id = request.POST.get('response_id')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        accuracy = request.POST.get('accuracy', 0)
        
        if not response_id or not latitude or not longitude:
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        response = get_object_or_404(RequestResponse, id=response_id)
        
        # Check permission
        if response.donor != request.user:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        # Update response location
        response.update_location(float(latitude), float(longitude))
        
        # Log location history
        DonorLocationHistory.objects.create(
            donor=request.user,
            request=response.request,
            latitude=float(latitude),
            longitude=float(longitude),
            accuracy_meters=float(accuracy) if accuracy else None,
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Location updated',
        })
    except Exception as e:
        logger.error(f'Error updating location: {str(e)}', exc_info=True)
        return JsonResponse({'error': 'Failed to update location'}, status=500)


@login_required
def get_nearby_requests_api(request):
    """Get nearby blood requests for donors"""
    try:
        from accounts.models import User
        from math import radians, cos, sin, asin, sqrt
        
        # Get user location
        user = request.user
        if not user.latitude or not user.longitude:
            return JsonResponse({
                'error': 'Please update your location in profile',
                'needs_location': True
            }, status=400)
        
        # Get compatible blood groups
        compatible_groups = BloodRequestWorkflow.get_compatible_blood_groups(user.blood_group) if user.blood_group else []
        
        # Get active requests
        active_requests = BloodRequest.objects.filter(
            status__in=['active', 'partially_fulfilled'],
            patient_blood_group__in=compatible_groups if compatible_groups else ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
        )
        
        # Filter by distance
        nearby_requests = []
        user_lat = float(user.latitude)
        user_lng = float(user.longitude)
        
        for req in active_requests:
            # Calculate distance
            lat1, lon1 = radians(user_lat), radians(user_lng)
            lat2, lon2 = radians(float(req.latitude)), radians(float(req.longitude))
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            distance = c * 6371  # km
            
            if distance <= 50:  # 50km radius
                # Check if user already responded
                already_responded = RequestResponse.objects.filter(
                    request=req, donor=user
                ).exists()
                
                nearby_requests.append({
                    'id': req.id,
                    'patient_name': req.patient_name,
                    'blood_group': req.patient_blood_group,
                    'hospital': req.hospital_name,
                    'city': req.city,
                    'priority': req.priority,
                    'required_units': req.required_units,
                    'distance_km': round(distance, 2),
                    'already_responded': already_responded,
                    'created_at': req.created_at.isoformat(),
                })
        
        # Sort by distance
        nearby_requests.sort(key=lambda x: x['distance_km'])
        
        return JsonResponse({
            'success': True,
            'requests': nearby_requests,
            'total': len(nearby_requests),
        })
    except Exception as e:
        logger.error(f'Error getting nearby requests: {str(e)}', exc_info=True)
        return JsonResponse({'error': 'Failed to get nearby requests'}, status=500)


@login_required
def donor_gps_sender(request, response_id):
    """View for donor to share their GPS location while traveling to donate"""
    from blood_requests_app.models import BloodRequestResponse
    
    try:
        response = BloodRequestResponse.objects.get(id=response_id, donor=request.user)
    except BloodRequestResponse.DoesNotExist:
        messages.error(request, 'Response not found')
        return redirect('/requests/track-request-dashboard/')
    
    blood_request = response.blood_request
    
    context = {
        'response': response,
        'request': blood_request,
        'donor': request.user,
        'hospital_latitude': float(blood_request.latitude) if blood_request.latitude else 28.6139,
        'hospital_longitude': float(blood_request.longitude) if blood_request.longitude else 77.2090,
    }
    
    return render(request, 'requests/donor_gps_sender.html', context)


@login_required
def track_request_zomato(request, request_id):
    """Zomato-style tracking view for blood requests"""
    from blood_requests_app.models import BloodRequest
    
    try:
        blood_request = BloodRequest.objects.get(id=request_id)
    except BloodRequest.DoesNotExist:
        messages.error(request, 'Request not found')
        return redirect('/requests/track/')
    
    # Get all responses for this request
    responses = blood_request.responses.filter(status='accepted').select_related('donor')
    
    # Calculate current step based on status
    status_to_step = {
        'pending': 1,
        'verified': 2,
        'approved': 2,
        'active': 3,
        'partially_fulfilled': 4,
        'fulfilled': 5,
        'cancelled': 0,
        'expired': 0,
    }
    current_step = status_to_step.get(blood_request.status, 1)
    
    # Get matched donors using smart matching algorithm
    matched_donors = []
    if blood_request.status in ['active', 'approved']:
        try:
            matched_donors = blood_request.find_matching_donors(max_distance_km=50, limit=10)
        except Exception as e:
            logger.error(f'Error finding matched donors: {str(e)}')
    
    context = {
        'blood_request': blood_request,
        'responses': responses,
        'current_step': current_step,
        'matched_donors': matched_donors,
    }
    
    return render(request, 'requests/track_request_zomato.html', context)


@login_required
def manage_all_requests(request):
    """View to manage all blood requests with filtering and pagination"""
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    
    # Get all requests
    requests_list = BloodRequest.objects.all().order_by('-created_at')
    
    # Calculate stats
    total_count = requests_list.count()
    active_count = requests_list.filter(status='active').count()
    pending_count = requests_list.filter(status='pending').count()
    fulfilled_count = requests_list.filter(status='fulfilled').count()
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(requests_list, 10)  # 10 requests per page
    
    try:
        requests_page = paginator.page(page)
    except PageNotAnInteger:
        requests_page = paginator.page(1)
    except EmptyPage:
        requests_page = paginator.page(paginator.num_pages)
    
    context = {
        'requests': requests_page,
        'page_obj': requests_page,
        'total_count': total_count,
        'active_count': active_count,
        'pending_count': pending_count,
        'fulfilled_count': fulfilled_count,
    }
    
    return render(request, 'requests/manage_all_requests.html', context)


@login_required
def analytics_dashboard(request):
    """Analytics dashboard view for blood requests"""
    from .analytics import RequestAnalytics
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Get time filter from request
        days = int(request.GET.get('days', 30))
        
        # Only staff users can see global analytics, others see their own
        if request.user.is_staff:
            stats = RequestAnalytics.get_dashboard_stats(days=days)
        else:
            stats = RequestAnalytics.get_dashboard_stats(user=request.user, days=days)
        
        context = {
            'stats': stats,
            'days': days,
        }
        
        return render(request, 'requests/analytics_dashboard.html', context)
    except Exception as e:
        logger.error(f'Analytics dashboard error: {str(e)}', exc_info=True)
        messages.error(request, 'Error loading analytics. Please try again later.')
        return redirect('/accounts/dashboard/')


@login_required
@require_POST
def submit_donor_rating(request):
    """Submit a rating for a donor after donation completion"""
    from django.http import JsonResponse
    from .models import DonorRating
    
    try:
        donor_id = request.POST.get('donor_id')
        blood_request_id = request.POST.get('blood_request_id')
        rating = int(request.POST.get('rating'))
        comment = request.POST.get('comment', '')
        
        # Validate rating
        if rating < 1 or rating > 5:
            return JsonResponse({
                'success': False,
                'error': 'Rating must be between 1 and 5'
            }, status=400)
        
        # Get donor and request
        donor = User.objects.get(id=donor_id)
        blood_request = BloodRequest.objects.get(id=blood_request_id)
        
        # Check if rating already exists
        existing_rating = DonorRating.objects.filter(
            donor=donor,
            rater=request.user,
            blood_request=blood_request
        ).first()
        
        if existing_rating:
            # Update existing rating
            existing_rating.rating = rating
            existing_rating.comment = comment
            existing_rating.save()
            created = False
        else:
            # Create new rating
            DonorRating.objects.create(
                donor=donor,
                rater=request.user,
                blood_request=blood_request,
                rating=rating,
                comment=comment
            )
            created = True
        
        # Calculate donor's average rating
        avg_rating = DonorRating.objects.filter(donor=donor).aggregate(
            avg_rating=Avg('rating')
        )['avg_rating'] or 0
        
        return JsonResponse({
            'success': True,
            'message': 'Rating submitted successfully',
            'average_rating': round(avg_rating, 1),
            'created': created
        })
        
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Donor not found'
        }, status=404)
    except BloodRequest.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Blood request not found'
        }, status=404)
    except Exception as e:
        logger.error(f'Error submitting rating: {str(e)}')
        return JsonResponse({
            'success': False,
            'error': 'Failed to submit rating'
        }, status=500)


@login_required
def admin_donors_page(request):
    """Admin page to manage and view all donors"""
    from django.contrib.auth.decorators import user_passes_test
    from accounts.models import User
    from django.db.models import Q
    
    # Check if user is staff
    if not request.user.is_staff:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('/accounts/dashboard/')
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    blood_group = request.GET.get('blood_group', '')
    city = request.GET.get('city', '')
    is_verified = request.GET.get('is_verified', '')
    
    # Base queryset - only donors
    donors = User.objects.filter(user_type='donor')
    
    # Apply filters
    if search_query:
        donors = donors.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(phone_number__icontains=search_query)
        )
    
    if blood_group:
        donors = donors.filter(blood_group=blood_group)
    
    if city:
        donors = donors.filter(city__icontains=city)
    
    if is_verified:
        donors = donors.filter(is_verified=is_verified == 'true')
    
    # Order by most recent
    donors = donors.order_by('-date_joined')
    
    # Get unique blood groups and cities for filters
    blood_groups = User.objects.filter(user_type='donor').values_list('blood_group', flat=True).distinct().order_by('blood_group')
    cities = User.objects.filter(user_type='donor').values_list('city', flat=True).distinct().order_by('city')
    
    context = {
        'donors': donors[:100],  # Limit to 100 for performance
        'total_donors': donors.count(),
        'blood_groups': blood_groups,
        'cities': cities,
        'search_query': search_query,
        'selected_blood_group': blood_group,
        'selected_city': city,
        'selected_verified': is_verified,
    }
    
    return render(request, 'admin/donors.html', context)


@login_required
def admin_users_page(request):
    """Admin page to manage all users"""
    from accounts.models import User
    from django.db.models import Q
    
    # Check if user is staff
    if not request.user.is_staff:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('/accounts/dashboard/')
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    user_type = request.GET.get('user_type', '')
    is_verified = request.GET.get('is_verified', '')
    
    # Base queryset
    users = User.objects.all()
    
    # Apply filters
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    if user_type:
        users = users.filter(user_type=user_type)
    
    if is_verified:
        users = users.filter(is_verified=is_verified == 'true')
    
    # Order by most recent
    users = users.order_by('-date_joined')
    
    context = {
        'users': users[:100],  # Limit to 100 for performance
        'total_users': users.count(),
        'user_types': ['donor', 'hospital', 'admin', 'volunteer'],
        'search_query': search_query,
        'selected_user_type': user_type,
        'selected_verified': is_verified,
    }
    
    return render(request, 'admin/users.html', context)


@login_required
def admin_analytics_page(request):
    """Admin analytics dashboard with comprehensive statistics"""
    from .analytics import RequestAnalytics
    from accounts.models import User
    from django.db.models import Count, Q, Avg
    from django.utils import timezone
    from datetime import timedelta
    import logging
    logger = logging.getLogger(__name__)
    
    # Check if user is staff
    if not request.user.is_staff:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('/accounts/dashboard/')
    
    try:
        # Get time filter
        days = int(request.GET.get('days', 30))
        
        # Get comprehensive analytics
        stats = RequestAnalytics.get_dashboard_stats(days=days)
        
        # Additional user statistics
        total_users = User.objects.count()
        new_users_period = User.objects.filter(
            date_joined__gte=timezone.now() - timedelta(days=days)
        ).count()
        
        users_by_type = User.objects.values('user_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        users_by_blood_group = User.objects.filter(
            user_type='donor'
        ).values('blood_group').annotate(
            count=Count('id')
        ).order_by('blood_group')
        
        context = {
            'stats': stats,
            'days': days,
            'total_users': total_users,
            'new_users_period': new_users_period,
            'users_by_type': users_by_type,
            'users_by_blood_group': users_by_blood_group,
        }
        
        return render(request, 'admin/analytics.html', context)
    except Exception as e:
        logger.error(f'Admin analytics error: {str(e)}', exc_info=True)
        messages.error(request, 'Error loading analytics. Please try again later.')
        return redirect('/accounts/dashboard/')
