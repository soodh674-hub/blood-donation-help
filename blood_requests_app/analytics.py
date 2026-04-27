"""
Analytics module for blood request system
Provides comprehensive statistics and insights
"""
from django.db.models import Count, Avg, Q
from datetime import timedelta, datetime
from django.utils import timezone
from .models import BloodRequest, RequestResponse


class RequestAnalytics:
    """Analytics for blood requests"""
    
    @classmethod
    def get_dashboard_stats(cls, user=None, days=30):
        """Get comprehensive analytics"""
        start_date = timezone.now() - timedelta(days=days)
        
        # Base queryset
        requests = BloodRequest.objects.filter(created_at__gte=start_date)
        if user:
            requests = requests.filter(requester=user)
        
        total = requests.count()
        fulfilled = requests.filter(status='fulfilled').count()
        active = requests.filter(status__in=['active', 'partially_fulfilled']).count()
        pending = requests.filter(status='pending').count()
        
        return {
            'total_requests': total,
            'fulfilled_requests': fulfilled,
            'active_requests': active,
            'pending_requests': pending,
            'fulfillment_rate': (fulfilled / total * 100) if total > 0 else 0,
            'avg_response_time': cls.get_avg_response_time(requests),
            'avg_fulfillment_time': cls.get_avg_fulfillment_time(requests),
            'by_blood_group': cls.get_by_blood_group(requests),
            'by_priority': cls.get_by_priority(requests),
            'by_city': cls.get_by_city(requests),
            'trend_data': cls.get_trend_data(requests, days),
            'donor_stats': cls.get_donor_stats(start_date),
        }
    
    @classmethod
    def get_by_blood_group(cls, requests):
        """Requests by blood group"""
        return list(requests.values('patient_blood_group')
                   .annotate(count=Count('id'))
                   .order_by('-count'))
    
    @classmethod
    def get_by_priority(cls, requests):
        """Requests by priority"""
        return list(requests.values('priority')
                   .annotate(count=Count('id'))
                   .order_by('-count'))
    
    @classmethod
    def get_by_city(cls, requests, limit=10):
        """Top cities by request count"""
        return list(requests.values('city')
                   .annotate(count=Count('id'))
                   .order_by('-count')[:limit])
    
    @classmethod
    def get_trend_data(cls, requests, days):
        """Daily request trends"""
        trends = []
        for i in range(days):
            date = timezone.now() - timedelta(days=days-i-1)
            count = requests.filter(
                created_at__date=date.date()
            ).count()
            trends.append({
                'date': date.strftime('%Y-%m-%d'),
                'count': count
            })
        return trends
    
    @classmethod
    def get_donor_stats(cls, start_date):
        """Donor activity statistics"""
        responses = RequestResponse.objects.filter(responded_at__gte=start_date)
        
        return {
            'total_responses': responses.count(),
            'interested': responses.filter(status='interested').count(),
            'en_route': responses.filter(status='en_route').count(),
            'arrived': responses.filter(status='arrived').count(),
            'donated': responses.filter(status='donated').count(),
        }
    
    @classmethod
    def get_avg_response_time(cls, requests):
        """Get average response time in hours"""
        responses = RequestResponse.objects.filter(
            request__in=requests,
            responded_at__isnull=False
        )
        
        if not responses.exists():
            return 0
        
        total_hours = 0
        count = 0
        
        for response in responses:
            if response.request.created_at:
                hours = (response.responded_at - response.request.created_at).total_seconds() / 3600
                total_hours += hours
                count += 1
        
        return round(total_hours / count, 2) if count > 0 else 0
    
    @classmethod
    def get_avg_fulfillment_time(cls, requests):
        """Get average fulfillment time in hours"""
        fulfilled_requests = requests.filter(
            status='fulfilled',
            fulfilled_at__isnull=False,
            created_at__isnull=False
        )
        
        if not fulfilled_requests.exists():
            return 0
        
        total_hours = 0
        count = 0
        
        for request in fulfilled_requests:
            hours = (request.fulfilled_at - request.created_at).total_seconds() / 3600
            total_hours += hours
            count += 1
        
        return round(total_hours / count, 2) if count > 0 else 0
