from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Count
from .models import BloodRequest, RequestResponse
from accounts.models import User
import json

@login_required
def enhanced_dashboard_view(request):
    """Enhanced dashboard view with real-time updates"""
    try:
        # Get user location
        user_lat = getattr(request.user, 'latitude', None)
        user_lng = getattr(request.user, 'longitude', None)
        
        # Get live blood requests
        live_requests = BloodRequest.objects.filter(
            status__in=['active', 'partially_fulfilled']
        ).select_related('requester').order_by('-created_at')[:10]
        
        # Calculate distances for requests
        requests_with_distance = []
        for req in live_requests:
            distance = None
            if user_lat and user_lng and hasattr(req, 'latitude') and hasattr(req, 'longitude'):
                distance = calculate_distance(
                    user_lat, user_lng,
                    req.latitude, req.longitude
                )
            
            requests_with_distance.append({
                'request': req,
                'distance': round(distance, 1) if distance else None,
                'time_ago': get_time_ago(req.created_at)
            })
        
        # Get interested donors (users who responded to user's requests)
        user_requests = BloodRequest.objects.filter(requester=request.user)
        interested_donors = RequestResponse.objects.filter(
            blood_request__in=user_requests,
            status='accepted'
        ).select_related('donor').order_by('-response_time')[:10]
        
        # Get nearby donors
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
                        nearby_donors.append({
                            'donor': donor,
                            'distance': round(distance, 1)
                        })
        
        # Sort nearby donors by distance
        nearby_donors.sort(key=lambda x: x['distance'])
        nearby_donors = nearby_donors[:5]  # Limit to 5
        
        context = {
            'live_requests': requests_with_distance,
            'interested_donors': interested_donors,
            'nearby_donors': nearby_donors,
            'user_location': {
                'lat': user_lat,
                'lng': user_lng
            }
        }
        
        return render(request, 'requests/track_request_dashboard.html', context)

    except Exception as e:
        # Fallback to basic dashboard
        return render(request, 'requests/track_request_dashboard.html', {
            'live_requests': [],
            'interested_donors': [],
            'nearby_donors': []
        })

@login_required
def enhanced_track_request_view(request, request_id=None):
    """Enhanced track request view with real-time tracking"""
    try:
        if request_id:
            # Track specific request
            blood_request = get_object_or_404(BloodRequest, id=request_id)
            
            # Check if user can track this request
            can_track = (
                blood_request.requester == request.user or
                RequestResponse.objects.filter(
                    blood_request=blood_request,
                    donor=request.user
                ).exists()
            )
            
            if not can_track:
                return render(request, 'errors/403.html', status=403)
            
            # Get donor responses
            responses = RequestResponse.objects.filter(
                blood_request=blood_request
            ).select_related('donor').order_by('-response_time')
            
            # Calculate distances for donors
            responses_with_distance = []
            for response in responses:
                distance = None
                if (hasattr(blood_request, 'latitude') and hasattr(blood_request, 'longitude') and
                    hasattr(response.donor, 'latitude') and hasattr(response.donor, 'longitude')):
                    distance = calculate_distance(
                        blood_request.latitude, blood_request.longitude,
                        response.donor.latitude, response.donor.longitude
                    )
                
                responses_with_distance.append({
                    'response': response,
                    'distance': round(distance, 1) if distance else None
                })
            
            context = {
                'request': blood_request,
                'responses': responses_with_distance,
                'can_manage': blood_request.requester == request.user,
                'user_lat': getattr(request.user, 'latitude', None),
                'user_lng': getattr(request.user, 'longitude', None)
            }
            
            return render(request, 'requests/track_request_enhanced.html', context)
        else:
            # Show user's requests to track
            user_requests = BloodRequest.objects.filter(
                requester=request.user
            ).order_by('-created_at')
            
            context = {
                'requests': user_requests,
                'tracking_page': True
            }
            
            return render(request, 'requests/track_request_list.html', context)
            
    except Exception as e:
        return render(request, 'errors/500.html', status=500)

@login_required
def enhanced_chat_view(request, contact_id=None):
    """Enhanced chat view with real-time messaging"""
    try:
        if contact_id:
            # Chat with specific contact
            contact = get_object_or_404(User, id=contact_id)
            
            # Get chat history
            from .models_chat import ChatMessage
            messages = ChatMessage.objects.filter(
                Q(sender=request.user, receiver=contact) |
                Q(sender=contact, receiver=request.user)
            ).order_by('created_at')
            
            # Get all contacts for sidebar
            all_contacts = User.objects.filter(
                Q(is_donor=True) | Q(id__in=ChatMessage.objects.filter(
                    Q(sender=request.user) | Q(receiver=request.user)
                ).values_list('sender', 'receiver'))
            ).distinct().exclude(id=request.user.id)
            
            # Add online status and unread counts
            contacts_with_info = []
            for user_contact in all_contacts:
                unread_count = ChatMessage.objects.filter(
                    sender=user_contact,
                    receiver=request.user,
                    is_read=False
                ).count()
                
                contacts_with_info.append({
                    'user': user_contact,
                    'unread_count': unread_count,
                    'is_online': getattr(user_contact, 'is_online', False)
                })
            
            context = {
                'contact': contact,
                'messages': messages,
                'contacts': contacts_with_info,
                'current_contact_id': contact_id
            }
            
            return render(request, 'requests/chat_enhanced.html', context)
        else:
            # Show contacts list
            from .models_chat import ChatMessage
            contacts = User.objects.filter(
                Q(is_donor=True) | Q(id__in=ChatMessage.objects.filter(
                    Q(sender=request.user) | Q(receiver=request.user)
                ).values_list('sender', 'receiver'))
            ).distinct().exclude(id=request.user.id)
            
            # Add unread counts
            contacts_with_info = []
            for user_contact in contacts:
                unread_count = ChatMessage.objects.filter(
                    sender=user_contact,
                    receiver=request.user,
                    is_read=False
                ).count()
                
                contacts_with_info.append({
                    'user': user_contact,
                    'unread_count': unread_count,
                    'is_online': getattr(user_contact, 'is_online', False)
                })
            
            context = {
                'contacts': contacts_with_info
            }
            
            return render(request, 'requests/chat_list.html', context)
            
    except Exception as e:
        return render(request, 'errors/500.html', status=500)

@login_required
def find_donors_view(request):
    """Enhanced find donors view with advanced filters"""
    try:
        # Get filter parameters
        city = request.GET.get('city', '')
        blood_group = request.GET.get('blood_group', '')
        distance = request.GET.get('distance', '')
        
        # Get user location
        user_lat = getattr(request.user, 'latitude', None)
        user_lng = getattr(request.user, 'longitude', None)
        
        # Start with base queryset
        donors = User.objects.filter(
            is_donor=True,
            is_active=True
        ).exclude(id=request.user.id)
        
        # Apply filters
        if city:
            donors = donors.filter(city__icontains=city)
        
        if blood_group and blood_group != 'all':
            donors = donors.filter(blood_group=blood_group)
        
        # Calculate distances and filter by distance
        max_distance = None
        if distance and distance != 'any':
            if distance == 'under_2':
                max_distance = 2
            elif distance == '2_to_5':
                max_distance = 5
            elif distance == '5_to_10':
                max_distance = 10
        
        donors_with_distance = []
        for donor in donors:
            donor_distance = None
            if (user_lat and user_lng and 
                hasattr(donor, 'latitude') and hasattr(donor, 'longitude')):
                donor_distance = calculate_distance(
                    user_lat, user_lng,
                    donor.latitude, donor.longitude
                )
            
            # Filter by distance if specified
            if max_distance and donor_distance and donor_distance > max_distance:
                continue
            
            donors_with_distance.append({
                'donor': donor,
                'distance': round(donor_distance, 1) if donor_distance else None
            })
        
        # Sort by distance if available
        if user_lat and user_lng:
            donors_with_distance.sort(key=lambda x: (x['distance'] is None, x['distance']))
        
        context = {
            'donors': donors_with_distance,
            'filters': {
                'city': city,
                'blood_group': blood_group,
                'distance': distance
            },
            'total_count': len(donors_with_distance)
        }
        
        return render(request, 'requests/find_donors.html', context)
        
    except Exception as e:
        return render(request, 'errors/500.html', status=500)

# Helper functions
def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in kilometers"""
    import math
    
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
