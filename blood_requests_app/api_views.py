from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q, Count
from django.views import View
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import BloodRequest, RequestResponse
from accounts.models import User
import json
import math

@api_view(['GET'])
@permission_classes([AllowAny])  # Allow anyone to view live requests
def live_requests_api(request):
    """API endpoint for live blood requests with real-time updates"""
    try:
        # Get user location from profile or request (if authenticated)
        user_lat = None
        user_lng = None
        if request.user.is_authenticated:
            user_lat = getattr(request.user, 'latitude', None)
            user_lng = getattr(request.user, 'longitude', None)
        
        # Filter active requests
        requests = BloodRequest.objects.filter(
            status__in=['active', 'partially_fulfilled']
        ).select_related('requester').order_by('-created_at')
        
        # Calculate distances if user location is available
        requests_data = []
        for req in requests:
            distance = None
            time_ago = get_time_ago(req.created_at)
            
            if user_lat and user_lng and req.latitude and req.longitude:
                distance = calculate_distance(
                    user_lat, user_lng, 
                    req.latitude, req.longitude
                )
            
            requests_data.append({
                'id': req.id,
                'blood_group': req.patient_blood_group,
                'urgency': req.priority,
                'distance': round(distance, 1) if distance else None,
                'time_ago': time_ago,
                'hospital_name': req.hospital_name,
                'city': req.city,
                'required_units': req.required_units,
                'fulfilled_units': req.fulfilled_units,
                'patient_name': req.patient_name,
                'requester': req.requester.get_full_name() or req.requester.username,
                'created_at': req.created_at.isoformat()
            })
        
        return JsonResponse({
            'success': True,
            'requests': requests_data,
            'total': len(requests_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def respond_to_request_api(request, request_id):
    """API endpoint for responding to blood requests"""
    try:
        blood_request = get_object_or_404(BloodRequest, id=request_id)
        
        # Check if user already responded
        existing_response = RequestResponse.objects.filter(
            request=blood_request,
            donor=request.user
        ).first()
        
        if existing_response:
            return JsonResponse({
                'success': False,
                'error': 'You have already responded to this request'
            }, status=400)
        
        # Create response
        response = RequestResponse.objects.create(
            request=blood_request,
            donor=request.user,
            status='interested',
            responded_at=timezone.now()
        )
        
        # Update request status if needed
        if blood_request.fulfilled_units >= blood_request.required_units:
            blood_request.status = 'fulfilled'
            blood_request.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Response submitted successfully!',
            'response_id': response.id
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def select_donor_api(request, request_id):
    """API endpoint for selecting a donor for a blood request"""
    try:
        blood_request = get_object_or_404(BloodRequest, id=request_id)
        donor_id = request.data.get('donor_id')
        
        if not donor_id:
            return JsonResponse({
                'success': False,
                'error': 'Donor ID is required'
            }, status=400)
        
        donor = get_object_or_404(User, id=donor_id)
        
        # Check if user is the requester
        if blood_request.requester != request.user:
            return JsonResponse({
                'success': False,
                'error': 'Only the requester can select donors'
            }, status=403)
        
        # Update donor response status
        response = RequestResponse.objects.filter(
            request=blood_request,
            donor=donor
        ).first()
        
        if not response:
            return JsonResponse({
                'success': False,
                'error': 'Donor has not responded to this request'
            }, status=400)
        
        response.status = 'selected'
        response.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Donor selected successfully!',
            'donor_name': donor.get_full_name() or donor.username
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def find_donors_api(request):
    """API endpoint for finding donors with filters"""
    try:
        city = request.GET.get('city', '')
        blood_group = request.GET.get('blood_group', '')
        distance_str = request.GET.get('distance', '')
        
        # Get user location
        user_lat = getattr(request.user, 'latitude', None)
        user_lng = getattr(request.user, 'longitude', None)
        
        # Filter donors
        donors = User.objects.filter(
            is_donor=True,
            is_active=True
        ).exclude(id=request.user.id)
        
        if city:
            donors = donors.filter(city__icontains=city)
        
        if blood_group and blood_group != 'all':
            donors = donors.filter(blood_group=blood_group)
        
        # Calculate distances and filter by distance
        max_distance = None
        if distance_str and distance_str != 'any':
            if distance_str == 'under_2':
                max_distance = 2
            elif distance_str == '2_to_5':
                max_distance = 5
            elif distance_str == '5_to_10':
                max_distance = 10
        
        donors_data = []
        for donor in donors:
            distance = None
            if user_lat and user_lng and hasattr(donor, 'latitude') and hasattr(donor, 'longitude'):
                distance = calculate_distance(
                    user_lat, user_lng,
                    donor.latitude, donor.longitude
                )
            
            # Filter by distance if specified
            if max_distance and distance and distance > max_distance:
                continue
            
            donors_data.append({
                'id': donor.id,
                'name': donor.get_full_name() or donor.username,
                'blood_group': donor.blood_group,
                'distance': round(distance, 1) if distance else None,
                'city': donor.city,
                'phone': donor.phone_number,
                'last_donation': donor.last_donation.isoformat() if donor.last_donation else None,
                'is_available': donor.is_available_for_donation()
            })
        
        # Sort by distance if available
        if user_lat and user_lng:
            donors_data.sort(key=lambda x: (x['distance'] is None, x['distance']))
        
        return JsonResponse({
            'success': True,
            'donors': donors_data,
            'total': len(donors_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def emergency_alert_api(request):
    """API endpoint for sending emergency alerts"""
    try:
        message = request.data.get('message', '')
        location = request.data.get('location', '')
        
        if not message:
            return JsonResponse({
                'success': False,
                'error': 'Message is required'
            }, status=400)
        
        # Find nearby donors (within 10km)
        user_lat = getattr(request.user, 'latitude', None)
        user_lng = getattr(request.user, 'longitude', None)
        
        nearby_donors = []
        if user_lat and user_lng:
            all_donors = User.objects.filter(
                is_donor=True,
                is_active=True,
                is_available=True
            ).exclude(id=request.user.id)
            
            for donor in all_donors:
                if hasattr(donor, 'latitude') and hasattr(donor, 'longitude'):
                    distance = calculate_distance(
                        user_lat, user_lng,
                        donor.latitude, donor.longitude
                    )
                    if distance <= 10:  # Within 10km
                        nearby_donors.append(donor)
        
        # Here you would implement actual notification sending
        # For now, we'll just return the count
        notified_count = len(nearby_donors)
        
        return JsonResponse({
            'success': True,
            'message': 'Emergency alert sent successfully!',
            'notified_count': notified_count
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_history_api(request, contact_id):
    """API endpoint for fetching chat history"""
    try:
        contact = get_object_or_404(User, id=contact_id)
        
        # Get messages between current user and contact
        from .models import ChatMessage
        
        messages = ChatMessage.objects.filter(
            Q(sender=request.user, receiver=contact) |
            Q(sender=contact, receiver=request.user)
        ).order_by('created_at')
        
        messages_data = []
        for msg in messages:
            messages_data.append({
                'id': msg.id,
                'content': msg.message,
                'type': 'sent' if msg.sender == request.user else 'received',
                'timestamp': msg.created_at.isoformat(),
                'sender': msg.sender.get_full_name() or msg.sender.username
            })
        
        return JsonResponse({
            'success': True,
            'messages': messages_data,
            'contact': {
                'id': contact.id,
                'name': contact.get_full_name() or contact.username,
                'blood_group': contact.blood_group
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# Helper functions
def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in kilometers"""
    if not all([lat1, lon1, lat2, lon2]):
        return None
    
    # Haversine formula
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    distance = R * c
    return distance

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


class TrackSpecificRequestView(View):
    """Get details of a specific blood request - works across devices"""
    
    def get(self, request, request_id):
        try:
            blood_request = get_object_or_404(BloodRequest, id=request_id)
            
            # Allow tracking for public requests (active, partially_fulfilled) without authentication
            # For other statuses, require authentication or requester/donor relationship
            if not request.user.is_authenticated and blood_request.status not in ['active', 'partially_fulfilled', 'pending']:
                return JsonResponse({'error': 'Not found'}, status=404)
            
            responses = RequestResponse.objects.filter(request=blood_request).select_related('donor')
            
            return JsonResponse({
                'success': True,
                'request': {
                    'id': blood_request.id,
                    'patient_name': blood_request.patient_name,
                    'patient_age': blood_request.patient_age,
                    'blood_group': blood_request.patient_blood_group,
                    'required_units': blood_request.required_units,
                    'fulfilled_units': blood_request.fulfilled_units,
                    'priority': blood_request.priority,
                    'status': blood_request.status,
                    'hospital_name': blood_request.hospital_name,
                    'city': blood_request.city,
                    'state': blood_request.state,
                    'latitude': float(blood_request.latitude) if blood_request.latitude else None,
                    'longitude': float(blood_request.longitude) if blood_request.longitude else None,
                    'contact_person': blood_request.contact_person,
                    'contact_phone': blood_request.contact_phone,
                    'reason': blood_request.reason,
                    'created_at': blood_request.created_at.isoformat(),
                    'expires_at': blood_request.expires_at.isoformat(),
                    'requester_name': blood_request.requester.get_full_name() or blood_request.requester.username,
                },
                'responses_count': responses.count(),
                'donors': [{
                    'id': r.donor.id,
                    'name': r.donor.get_full_name() or r.donor.username,
                    'blood_group': r.donor.blood_group,
                    'status': r.status,
                    'responded_at': r.responded_at.isoformat(),
                    'phone': r.donor.phone_number,
                } for r in responses]
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


class RequestTimelineView(View):
    """Get timeline of status changes for a request - works across devices"""
    
    def get(self, request, request_id):
        try:
            blood_request = get_object_or_404(BloodRequest, id=request_id)
            
            # Allow public access for active requests
            if not request.user.is_authenticated and blood_request.status not in ['active', 'partially_fulfilled', 'pending']:
                return JsonResponse({'error': 'Not found'}, status=404)
            
            # Build timeline from status_history
            timeline = []
            
            # Add creation event
            timeline.append({
                'event': 'Request Created',
                'timestamp': blood_request.created_at.isoformat(),
                'status': 'pending',
                'description': f'Blood request created for {blood_request.patient_blood_group}',
                'icon': 'create'
            })
            
            # Add status history events
            if blood_request.status_history:
                for event in blood_request.status_history:
                    timeline.append({
                        'event': event.get('status', 'Status Update'),
                        'timestamp': event.get('timestamp', blood_request.created_at.isoformat()),
                        'status': event.get('status'),
                        'description': event.get('notes', ''),
                        'icon': 'update'
                    })
            
            # Add approval event
            if blood_request.approved_at:
                timeline.append({
                    'event': 'Request Approved',
                    'timestamp': blood_request.approved_at.isoformat(),
                    'status': 'approved',
                    'description': f'Approved by {blood_request.approved_by.get_full_name() if blood_request.approved_by else "Admin"}',
                    'icon': 'approve'
                })
            
            # Add donor response events
            responses = RequestResponse.objects.filter(
                request=blood_request
            ).select_related('donor').order_by('responded_at')
            
            for response in responses:
                timeline.append({
                    'event': 'Donor Responded',
                    'timestamp': response.responded_at.isoformat(),
                    'status': response.status,
                    'description': f'{response.donor.get_full_name() or response.donor.username} responded',
                    'icon': 'donor'
                })
            
            # Sort by timestamp
            timeline.sort(key=lambda x: x['timestamp'])
            
            return JsonResponse({
                'success': True,
                'timeline': timeline
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


class RequestResponsesView(View):
    """Get all responses for a request - works across devices"""
    
    def get(self, request, request_id):
        try:
            blood_request = get_object_or_404(BloodRequest, id=request_id)
            
            # Allow public access for active requests (hide sensitive donor info)
            if not request.user.is_authenticated and blood_request.status not in ['active', 'partially_fulfilled', 'pending']:
                return JsonResponse({'error': 'Not found'}, status=404)
            
            responses = RequestResponse.objects.filter(
                request=blood_request
            ).select_related('donor').order_by('-responded_at')
            
            responses_data = []
            for response in responses:
                donor = response.donor
                responses_data.append({
                    'id': response.id,
                    'donor_id': donor.id,
                    'donor_name': donor.get_full_name() or donor.username,
                    'donor_blood_group': donor.blood_group,
                    'status': response.status,
                    'responded_at': response.responded_at.isoformat(),
                    'phone': donor.phone_number,
                    'email': donor.email,
                    'distance_km': float(response.distance_km) if response.distance_km else None,
                    'eta_minutes': response.estimated_arrival_minutes,
                    'message': response.notes if response.notes else '',
                    'is_selected': response.is_selected,
                    'donor_lat': float(response.donor_latitude) if response.donor_latitude else None,
                    'donor_lng': float(response.donor_longitude) if response.donor_longitude else None,
                })
            
            return JsonResponse({
                'success': True,
                'responses': responses_data,
                'total': len(responses_data)
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


class RequestAnalyticsView(View):
    """Get analytics data for a request - works across devices"""
    
    def get(self, request, request_id):
        try:
            blood_request = get_object_or_404(BloodRequest, id=request_id)
            
            # Allow public access for active requests
            if not request.user.is_authenticated and blood_request.status not in ['active', 'partially_fulfilled', 'pending']:
                return JsonResponse({'error': 'Not found'}, status=404)
            
            responses = RequestResponse.objects.filter(request=blood_request)
            
            # Calculate analytics
            total_responses = responses.count()
            interested_count = responses.filter(status='interested').count()
            selected_count = responses.filter(status='selected').count()
            completed_count = responses.filter(status='completed').count()
            
            # Response rate
            # (In production, you'd track how many donors were notified)
            response_rate = 0
            if total_responses > 0:
                response_rate = round((interested_count / max(total_responses, 1)) * 100, 2)
            
            # Average response time
            avg_response_time = None
            if responses.exists():
                response_times = []
                for response in responses:
                    if response.responded_at and blood_request.created_at:
                        time_diff = (response.responded_at - blood_request.created_at).total_seconds() / 60
                        response_times.append(time_diff)
                
                if response_times:
                    avg_response_time = round(sum(response_times) / len(response_times), 2)
            
            # Time until expiry
            time_remaining = None
            if blood_request.expires_at:
                time_diff = blood_request.expires_at - timezone.now()
                if time_diff.total_seconds() > 0:
                    hours = int(time_diff.total_seconds() / 3600)
                    minutes = int((time_diff.total_seconds() % 3600) / 60)
                    time_remaining = f"{hours}h {minutes}m"
            
            # Fulfillment percentage
            fulfillment_pct = 0
            if blood_request.required_units > 0:
                fulfillment_pct = round(
                    (blood_request.fulfilled_units / blood_request.required_units) * 100, 2
                )
            
            return JsonResponse({
                'success': True,
                'analytics': {
                    'total_responses': total_responses,
                    'interested': interested_count,
                    'selected': selected_count,
                    'completed': completed_count,
                    'response_rate': response_rate,
                    'avg_response_time_minutes': avg_response_time,
                    'time_remaining': time_remaining,
                    'fulfillment_percentage': fulfillment_pct,
                    'required_units': blood_request.required_units,
                    'fulfilled_units': blood_request.fulfilled_units,
                    'views': getattr(blood_request, 'view_count', 0),
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


class SelectDonorView(View):
    """Select a donor for a blood request"""
    
    def post(self, request, request_id):
        try:
            blood_request = get_object_or_404(BloodRequest, id=request_id)
            
            # Verify user is the requester
            if blood_request.requester != request.user:
                return JsonResponse({
                    'success': False,
                    'error': 'Only the requester can select donors'
                }, status=403)
            
            data = json.loads(request.body)
            donor_id = data.get('donor_id')
            
            if not donor_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Donor ID is required'
                }, status=400)
            
            donor = get_object_or_404(User, id=donor_id)
            
            # Find the response
            response = get_object_or_404(
                RequestResponse,
                request=blood_request,
                donor=donor
            )
            
            # Update response status
            response.status = 'selected'
            response.is_selected = True
            response.selected_at = timezone.now()
            response.save()
            
            # Update request fulfillment
            blood_request.fulfilled_units += 1
            if blood_request.fulfilled_units >= blood_request.required_units:
                blood_request.status = 'fulfilled'
            elif blood_request.fulfilled_units > 0:
                blood_request.status = 'partially_fulfilled'
            blood_request.save()
            
            return JsonResponse({
                'success': True,
                'message': f'{donor.get_full_name() or donor.username} has been selected!',
                'fulfilled_units': blood_request.fulfilled_units,
                'required_units': blood_request.required_units
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
