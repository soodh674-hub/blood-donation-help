"""
Report user API for anti-fake system
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import User, UserReport
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def report_user(request):
    """
    Report a user for fake/scam behavior
    """
    try:
        reported_user_id = request.data.get('reported_user_id')
        reason = request.data.get('reason')
        description = request.data.get('description', '')
        
        if not reported_user_id or not reason:
            return Response(
                {'error': 'reported_user_id and reason are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get users
        reporter = request.user
        reported_user = get_object_or_404(User, id=reported_user_id, is_active=True)
        
        # Check if already reported
        if UserReport.objects.filter(reporter=reporter, reported_user=reported_user).exists():
            return Response(
                {'error': 'You have already reported this user'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create report
        report = UserReport.objects.create(
            reporter=reporter,
            reported_user=reported_user,
            reason=reason,
            description=description
        )
        
        logger.info(f"User {reporter.username} reported {reported_user.username} for {reason}")
        
        return Response({
            'success': True,
            'message': 'User reported successfully',
            'report_id': report.id
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error reporting user: {e}", exc_info=True)
        return Response(
            {'error': 'Failed to report user'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_trust_score(request, user_id):
    """
    Get trust score and report count for a user
    """
    try:
        user = get_object_or_404(User, id=user_id, is_active=True)
        
        return Response({
            'success': True,
            'trust_score': user.trust_score,
            'reports_count': user.reports_count,
            'donations_completed': user.donations_completed,
            'is_blocked': user.is_blocked,
            'is_verified': user.is_verified
        })
        
    except Exception as e:
        logger.error(f"Error getting trust score: {e}", exc_info=True)
        return Response(
            {'error': 'Failed to get trust score'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
