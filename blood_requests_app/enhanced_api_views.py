"""
Enhanced API views with improved error handling, caching, and performance.
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework.response import Response
from django.core.cache import cache
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta

from blood_requests_app.models import BloodRequest
from blood_requests_app.serializers import BloodRequestSerializer
from apps.core.database_optimizer import cache_query, log_slow_queries

logger = logging.getLogger(__name__)


class EnhancedUserRateThrottle(UserRateThrottle):
    """Enhanced rate limiter with better logging"""
    rate = '200/hour'
    
    def throttle_failure(self):
        """Log throttling failures"""
        logger.warning(f"Rate limit exceeded for user {self.get_cache_key(self.request, self.view)}")
        super().throttle_failure()


class EnhancedAnonRateThrottle(AnonRateThrottle):
    """Enhanced rate limiter for anonymous users"""
    rate = '50/hour'


@api_view(['GET'])
@permission_classes([AllowAny])
@throttle_classes([EnhancedAnonRateThrottle, EnhancedUserRateThrottle])
@log_slow_queries(threshold=0.2)
def get_active_requests(request):
    """
    Get active blood requests with caching and optimization
    
    Query params:
    - city: Filter by city
    - blood_group: Filter by blood group
    - priority: Filter by priority (normal, urgent, emergency)
    - page: Page number for pagination
    """
    cache_key = f"active_requests_{request.query_params.urlencode()}"
    
    # Try cache first
    cached_result = cache.get(cache_key)
    if cached_result:
        logger.debug("Cache hit for active requests")
        return Response(cached_result)
    
    try:
        # Build optimized query
        queryset = BloodRequest.objects.filter(
            status__in=['active', 'approved']
        ).select_related('requester')
        
        # Apply filters
        city = request.query_params.get('city')
        if city:
            queryset = queryset.filter(city__icontains=city)
        
        blood_group = request.query_params.get('blood_group')
        if blood_group:
            queryset = queryset.filter(patient_blood_group=blood_group)
        
        priority = request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Order by priority and urgency
        queryset = queryset.order_by('-priority', 'required_by')
        
        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = 20
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        total_count = queryset.count()
        requests = queryset[start_idx:end_idx]
        
        serializer = BloodRequestSerializer(requests, many=True)
        
        result = {
            'success': True,
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size,
            'data': serializer.data
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, result, 300)
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error fetching active requests: {e}")
        return Response({
            'success': False,
            'error': 'Failed to fetch requests',
            'detail': str(e) if request.user.is_superuser else None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
@throttle_classes([EnhancedAnonRateThrottle, EnhancedUserRateThrottle])
def get_request_stats(request):
    """Get statistics about blood requests"""
    try:
        cache_key = "request_stats"
        cached = cache.get(cache_key)
        
        if cached:
            return Response(cached)
        
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        
        stats = {
            'total_active': BloodRequest.objects.filter(status__in=['active', 'approved']).count(),
            'total_urgent': BloodRequest.objects.filter(status='active', priority='emergency').count(),
            'last_24h': BloodRequest.objects.filter(created_at__gte=last_24h).count(),
            'last_7d': BloodRequest.objects.filter(created_at__gte=last_7d).count(),
            'by_blood_group': {},
            'by_city': {}
        }
        
        # Blood group distribution
        blood_groups = BloodRequest.objects.filter(status='active').values('patient_blood_group').annotate(
            count=Count('id')
        ).order_by('-count')
        
        stats['by_blood_group'] = {item['patient_blood_group']: item['count'] for item in blood_groups}
        
        # City distribution (top 10)
        cities = BloodRequest.objects.filter(status='active').values('city').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        stats['by_city'] = {item['city']: item['count'] for item in cities}
        
        # Cache for 10 minutes
        cache.set(cache_key, stats, 600)
        
        return Response({
            'success': True,
            'data': stats
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error fetching request stats: {e}")
        return Response({
            'success': False,
            'error': 'Failed to fetch statistics'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_donation_history(request):
    """Get authenticated user's donation history"""
    try:
        user = request.user
        
        # Get requests created by user
        created_requests = BloodRequest.objects.filter(requester=user).order_by('-created_at')[:50]
        
        serializer = BloodRequestSerializer(created_requests, many=True)
        
        return Response({
            'success': True,
            'count': len(serializer.data),
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error fetching user donation history: {e}")
        return Response({
            'success': False,
            'error': 'Failed to fetch donation history'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([EnhancedUserRateThrottle])
def report_request_issue(request, request_id):
    """Report an issue with a blood request"""
    try:
        blood_request = BloodRequest.objects.get(id=request_id)
        
        issue_type = request.data.get('issue_type')
        description = request.data.get('description', '')
        
        if not issue_type:
            return Response({
                'success': False,
                'error': 'Issue type is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Log the issue (in production, save to database)
        logger.warning(
            f"Issue reported for request #{request_id} by user {request.user.id}: "
            f"{issue_type} - {description}"
        )
        
        # TODO: Save to database and notify admins
        
        return Response({
            'success': True,
            'message': 'Issue reported successfully'
        }, status=status.HTTP_200_OK)
        
    except BloodRequest.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Request not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error reporting issue: {e}")
        return Response({
            'success': False,
            'error': 'Failed to report issue'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
