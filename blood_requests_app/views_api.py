"""
API endpoints for blood request tracking
"""
import logging
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from .models import BloodRequest, ChatMessage, DonorRating
from donors.models import DonorAvailability
from .serializers import BloodRequestSerializer, ChatMessageSerializer, DonorRatingSerializer, DonorAvailabilitySerializer
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


class UserBloodRequestsView(APIView):
    """Get all blood requests created by the current user"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        try:
            logger.info(f'Fetching blood requests for user: {request.user.id} ({request.user.email})')
            
            # Get all requests created by this user
            user = request.user
            
            # Build filter conditions - match by requester ForeignKey first
            filters = Q(requester=user)
            
            # Also match by contact information as fallback
            full_name = user.get_full_name()
            logger.info(f'User full name: {full_name}')
            
            if full_name:
                filters |= Q(contact_person=full_name)
            
            # Match by phone number if user has one
            if hasattr(user, 'phone_number') and user.phone_number:
                logger.info(f'Matching by phone: {user.phone_number}')
                filters |= Q(contact_phone=user.phone_number)
            
            # Match by email
            if user.email:
                logger.info(f'Matching by email: {user.email}')
                filters |= Q(contact_email=user.email)
            
            logger.info(f'Executing query with filters')
            requests_list = BloodRequest.objects.filter(filters).distinct().order_by('-created_at')[:50]  # Limit to last 50
            logger.info(f'Found {requests_list.count()} requests for user')
            
            serializer = BloodRequestSerializer(requests_list, many=True)
            return Response({
                'success': True,
                'requests': serializer.data,
                'count': len(requests_list)
            })
            
        except Exception as e:
            logger.error(f'Error fetching user requests: {str(e)}', exc_info=True)
            return Response({
                'success': False,
                'error': str(e),
                'message': 'An error occurred while fetching your blood requests'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TrackSpecificRequestView(APIView):
    """Track a specific blood request by ID"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, request_id):
        try:
            blood_request = BloodRequest.objects.filter(id=request_id).first()
            
            if not blood_request:
                return Response({
                    'success': False,
                    'error': 'Request not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = BloodRequestSerializer(blood_request)
            return Response({
                'success': True,
                'request': serializer.data
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, request_id):
        """Cancel/Delete a blood request"""
        try:
            blood_request = BloodRequest.objects.filter(id=request_id).first()
            
            if not blood_request:
                return Response({
                    'success': False,
                    'error': 'Request not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check if user owns this request
            if request.user.is_authenticated:
                if blood_request.requester != request.user:
                    return Response({
                        'success': False,
                        'error': 'You can only cancel your own requests'
                    }, status=status.HTTP_403_FORBIDDEN)
            
            # Update status to cancelled
            blood_request.status = 'cancelled'
            blood_request.save()
            
            return Response({
                'success': True,
                'message': 'Request cancelled successfully'
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e),
                'message': 'Failed to cancel request'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NearbyDonorsView(APIView):
    """Find nearby available donors for a blood request"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, request_id):
        try:
            blood_request = BloodRequest.objects.get(id=request_id)
            
            # Get available donors within 10km
            donors = DonorAvailability.objects.filter(
                status='available',
                current_latitude__isnull=False,
                current_longitude__isnull=False
            )
            
            nearby_donors = []
            for donor_avail in donors:
                # Calculate distance
                from math import radians, cos, sin, sqrt, atan2
                lat1, lon1 = float(donor_avail.current_latitude), float(donor_avail.current_longitude)
                lat2, lon2 = float(blood_request.latitude), float(blood_request.longitude)
                
                R = 6371
                dlat = radians(lat2 - lat1)
                dlon = radians(lon2 - lon1)
                a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
                c = 2 * atan2(sqrt(a), sqrt(1-a))
                distance = R * c
                
                if distance <= 10:  # Within 10km
                    serializer = DonorAvailabilitySerializer(
                        donor_avail, 
                        context={'request_id': request_id}
                    )
                    donor_data = serializer.data
                    donor_data['distance_km'] = round(distance, 2)
                    nearby_donors.append(donor_data)
            
            # Sort by distance
            nearby_donors.sort(key=lambda x: x['distance_km'])
            
            return Response({
                'success': True,
                'donors': nearby_donors[:20],  # Top 20 nearest
                'count': len(nearby_donors)
            })
        
        except BloodRequest.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Request not found'
            }, status=404)


class ChatHistoryView(APIView):
    """Get chat history for a request"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, request_id):
        messages = ChatMessage.objects.filter(
            request_id=request_id
        ).filter(
            Q(sender=request.user) | Q(receiver=request.user)
        ).order_by('timestamp')[:100]
        
        serializer = ChatMessageSerializer(messages, many=True)
        return Response({
            'success': True,
            'messages': serializer.data
        })


class MarkMessageReadView(APIView):
    """Mark chat messages as read"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        message_ids = request.data.get('message_ids', [])
        ChatMessage.objects.filter(
            id__in=message_ids,
            receiver=request.user
        ).update(is_read=True)
        
        return Response({'success': True})


class RateUserView(APIView):
    """Rate a donor or requester"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = DonorRatingSerializer(data=request.data)
        if serializer.is_valid():
            # Check if already rated
            existing = DonorRating.objects.filter(
                rater=request.user,
                rated_user_id=serializer.validated_data['rated_user'].id,
                request_id=serializer.validated_data['request'].id
            ).first()
            
            if existing:
                return Response({
                    'success': False,
                    'error': 'You have already rated this user for this request'
                }, status=400)
            
            rating = serializer.save(rater=request.user)
            return Response({
                'success': True,
                'rating': DonorRatingSerializer(rating).data
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=400)


class UpdateDonorLocationView(APIView):
    """Update donor's current location"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        
        if not latitude or not longitude:
            return Response({
                'success': False,
                'error': 'Latitude and longitude required'
            }, status=400)
        
        availability, _ = DonorAvailability.objects.get_or_create(donor=request.user)
        availability.current_latitude = latitude
        availability.current_longitude = longitude
        availability.status = 'available'
        availability.save()
        
        # Broadcast via WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"donor_location_{request.user.id}",
            {
                'type': 'location_update',
                'latitude': latitude,
                'longitude': longitude
            }
        )
        
        return Response({'success': True})


class ToggleDonorAvailabilityView(APIView):
    """Toggle donor availability status"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        status = request.data.get('status')
        if status not in ['available', 'on_donation', 'unavailable']:
            return Response({
                'success': False,
                'error': 'Invalid status'
            }, status=400)
        
        availability, _ = DonorAvailability.objects.get_or_create(donor=request.user)
        availability.status = status
        availability.save()
        
        return Response({
            'success': True,
            'status': availability.status
        })


class SendMessageView(APIView):
    """Send chat message via HTTP (fallback for non-WebSocket clients)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, request_id):
        try:
            message_text = request.data.get('message')
            receiver_id = request.data.get('receiver_id')
            
            if not message_text:
                return Response({
                    'success': False,
                    'error': 'Message text is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get the blood request
            blood_request = BloodRequest.objects.get(id=request_id)
            
            # Determine receiver (if not specified, send to requester)
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            if receiver_id:
                receiver = User.objects.get(id=receiver_id)
            else:
                receiver = blood_request.requester
            
            # Save message to database
            chat_message = ChatMessage.objects.create(
                request=blood_request,
                sender=request.user,
                receiver=receiver,
                message=message_text
            )
            
            # Try to broadcast via WebSocket if available
            try:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f'chat_{request_id}',
                    {
                        'type': 'chat_message',
                        'message': message_text,
                        'sender_id': request.user.id,
                        'sender_name': request.user.get_full_name() or request.user.username,
                        'timestamp': chat_message.timestamp.isoformat()
                    }
                )
            except Exception as ws_error:
                logger.warning(f'WebSocket broadcast failed (HTTP-only mode): {ws_error}')
            
            return Response({
                'success': True,
                'message': ChatMessageSerializer(chat_message).data
            })
        
        except BloodRequest.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Request not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f'Error sending message: {e}', exc_info=True)
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
