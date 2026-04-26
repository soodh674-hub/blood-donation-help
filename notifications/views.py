"""
Views for handling donation status updates and notifications
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import date
import json

from rest_framework import generics, permissions, authentication
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils.decorators import method_decorator

from donors.models import DonorAvailability
from .models import Notification
from .serializers import NotificationSerializer


@method_decorator(csrf_exempt, name='dispatch')
class NotificationListView(generics.ListAPIView):
    """
    List notifications for the authenticated user.
    Supports filtering by is_read.
    """
    serializer_class = NotificationSerializer
    authentication_classes = [authentication.SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        try:
            # Safety check for authenticated user
            if not self.request.user or not self.request.user.is_authenticated:
                return Notification.objects.none()
            
            queryset = Notification.objects.filter(user=self.request.user)
            is_read = self.request.query_params.get("is_read")
            if is_read is not None:
                if is_read.lower() == "true":
                    queryset = queryset.filter(is_read=True)
                elif is_read.lower() == "false":
                    queryset = queryset.filter(is_read=False)
            return queryset.order_by('-created_at')
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error in NotificationListView.get_queryset: {str(e)}", exc_info=True)
            # Return empty queryset instead of crashing
            return Notification.objects.none()


@login_required
@api_view(["POST"])
def mark_notification_read(request, pk):
    """
    Mark a notification as read.
    """
    try:
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.mark_as_read()
        return Response({"message": "Notification marked as read"})
    except Exception as e:
        return Response(
            {"detail": "An error occurred while marking notification as read."},
            status=500
        )


@login_required
@api_view(["GET"])
def get_blood_request_notifications(request):
    """
    Get blood request notifications for the user.
    """
    try:
        notifications = Notification.objects.filter(
            user=request.user,
            notification_type='blood_request'
        ).order_by('-created_at')[:10]
        
        data = [{
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'created_at': n.created_at.isoformat(),
            'is_read': n.is_read
        } for n in notifications]
        
        return Response(data)
    except Exception as e:
        return Response(
            {"detail": str(e)},
            status=500
        )


@login_required
@require_POST
def update_donation_status(request):
    """
    Handle donation status update from popup form
    
    Expects POST data:
    - current_status: 'available', 'unavailable', or 'not_eligible'
    - last_donation_date: optional date string
    - notes: optional text
    - remember_choice: optional (if present, don't show popup again today)
    """
    try:
        # Get donor availability profile
        availability, created = DonorAvailability.objects.get_or_create(
            donor=request.user,
            defaults={'is_available': True}
        )
        
        # Update status based on form data
        current_status = request.POST.get('current_status', 'available')
        
        if current_status == 'available':
            availability.is_available = True
            availability.reason_unavailable = ''
        elif current_status == 'unavailable':
            availability.is_available = False
            availability.reason_unavailable = request.POST.get('notes', '')
        elif current_status == 'not_eligible':
            availability.is_available = False
            availability.reason_unavailable = 'Medical reasons - Not eligible'
        
        # Update last donation date if provided
        last_donation_date_str = request.POST.get('last_donation_date')
        if last_donation_date_str:
            from donors.models import DonorHistory
            DonorHistory.objects.create(
                donor=request.user,
                donation_date=timezone.make_aware(timezone.datetime.strptime(last_donation_date_str, '%Y-%m-%d')),
                hospital='Self-reported',
                city='',
                blood_group=request.user.blood_group if hasattr(request.user, 'blood_group') else '',
                notes=request.POST.get('notes', '')
            )
        
        # Update last_status_update to today (this prevents popup from showing again today)
        availability.last_status_update = date.today()
        availability.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Status updated successfully!',
            'status': current_status,
            'next_eligible_check': 'tomorrow'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Failed to update status'
        }, status=500)


@login_required
def notification_list(request):
    """
    Display all notifications for the user with pagination
    """
    try:
        from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
        from notifications.models import Notification
        
        # Get unread notifications
        unread_notifications = Notification.objects.filter(
            user=request.user,
            is_read=False
        )[:10]  # Show last 10 unread
        
        # Get all notifications with pagination
        all_notifications = Notification.objects.filter(
            user=request.user
        ).order_by('-created_at')
        
        # Pagination
        page = request.GET.get('page', 1)
        paginator = Paginator(all_notifications, 20)  # 20 notifications per page
        
        try:
            notifications_page = paginator.page(page)
        except PageNotAnInteger:
            notifications_page = paginator.page(1)
        except EmptyPage:
            notifications_page = paginator.page(paginator.num_pages)
        
        context = {
            'unread_count': unread_notifications.count(),
            'notifications': notifications_page,
            'page_obj': notifications_page,
        }
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Return as JSON for AJAX requests
            return JsonResponse({
                'unread_count': context['unread_count'],
                'notifications': list(notifications_page.object_list.values()),
                'has_next': notifications_page.has_next(),
                'has_previous': notifications_page.has_previous(),
                'page': notifications_page.number,
                'num_pages': paginator.num_pages
            })
        
        return render(request, 'notifications/notification_list.html', context)
    except Exception as e:
        # Handle any errors gracefully
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'error': str(e),
                'unread_count': 0,
                'notifications': []
            }, status=500)
        # For regular requests, return empty page
        return render(request, 'notifications/notification_list.html', {
            'unread_count': 0,
            'notifications': [],
            'error': 'Unable to load notifications'
        })


@login_required
def mark_notification_as_read(request, notification_id):
    """
    Mark a specific notification as read
    """
    from notifications.models import Notification
    
    try:
        notification = Notification.objects.get(
            id=notification_id,
            user=request.user
        )
        notification.mark_as_read()
        
        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notification not found'}, status=404)


@login_required
def mark_all_notifications_read(request):
    """
    Mark all notifications as read
    """
    from notifications.models import Notification
    
    Notification.objects.filter(
        user=request.user,
        is_read=False
    ).update(is_read=True)
    
    return JsonResponse({'success': True})
