"""
Database optimization utilities for improved performance.
Includes query optimization, indexing, and caching strategies.
"""
import logging
from django.db import connection
from django.core.cache import cache
from functools import wraps
import time

logger = logging.getLogger(__name__)


def query_optimizer(func):
    """
    Decorator to optimize database queries by adding select_related and prefetch_related
    Usage: @query_optimizer('requester', 'approved_by')
    """
    def decorator(*args, **kwargs):
        related_fields = kwargs.pop('select_related', [])
        prefetch_fields = kwargs.pop('prefetch_related', [])
        
        queryset = func(*args, **kwargs)
        
        if hasattr(queryset, 'select_related') and related_fields:
            queryset = queryset.select_related(*related_fields)
        
        if hasattr(queryset, 'prefetch_related') and prefetch_fields:
            queryset = queryset.prefetch_related(*prefetch_fields)
        
        return queryset
    return decorator


def cache_query(timeout=300, key_prefix='query_cache'):
    """
    Decorator to cache database query results
    
    Args:
        timeout: Cache timeout in seconds (default 5 minutes)
        key_prefix: Prefix for cache key
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{key_prefix}_{func.__name__}_{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return result
            
            # Execute query
            logger.debug(f"Cache miss for {cache_key}, executing query")
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator


def log_slow_queries(threshold=0.1):
    """
    Decorator to log slow database queries
    
    Args:
        threshold: Time in seconds to consider a query slow (default 100ms)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            
            if elapsed > threshold:
                logger.warning(
                    f"Slow query detected: {func.__name__} took {elapsed:.3f}s"
                )
            
            return result
        return wrapper
    return decorator


class DatabaseOptimizer:
    """Utility class for database optimization"""
    
    @staticmethod
    def get_query_stats():
        """Get statistics about database queries"""
        return {
            'query_count': len(connection.queries),
            'total_query_time': sum(float(q['time']) for q in connection.queries),
            'queries': connection.queries[-10:] if connection.queries else []
        }
    
    @staticmethod
    def analyze_table(table_name):
        """Analyze a database table for optimization opportunities"""
        try:
            with connection.cursor() as cursor:
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
                
                # Get table size
                cursor.execute(f"""
                    SELECT pg_size_pretty(pg_total_relation_size('{table_name}'))
                """)
                table_size = cursor.fetchone()[0]
                
                # Get index information
                cursor.execute(f"""
                    SELECT indexname, indexdef 
                    FROM pg_indexes 
                    WHERE tablename = '{table_name}'
                """)
                indexes = cursor.fetchall()
                
                return {
                    'table': table_name,
                    'row_count': row_count,
                    'size': table_size,
                    'indexes': [{'name': idx[0], 'definition': idx[1]} for idx in indexes]
                }
        except Exception as e:
            logger.error(f"Failed to analyze table {table_name}: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def optimize_blood_request_queries():
        """Apply optimizations to common blood request queries"""
        optimizations = {
            'active_requests': {
                'select_related': ['requester', 'approved_by'],
                'prefetch_related': [],
                'filter': {'status__in': ['active', 'approved']},
                'order_by': ['-priority', 'required_by']
            },
            'user_requests': {
                'select_related': ['requester'],
                'prefetch_related': [],
                'order_by': ['-created_at']
            },
            'nearby_requests': {
                'select_related': ['requester'],
                'filter': {'status': 'active'},
                'order_by': ['required_by']
            }
        }
        
        return optimizations
    
    @staticmethod
    def clear_expired_data(days=30):
        """Clean up expired data to improve performance"""
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        try:
            # Clean up old notifications
            from notifications.models import Notification
            old_notifications = Notification.objects.filter(
                created_at__lt=cutoff_date,
                is_read=True
            )
            deleted_count = old_notifications.count()
            old_notifications.delete()
            logger.info(f"Cleaned up {deleted_count} old notifications")
            
            # Clean up expired blood requests
            from blood_requests_app.models import BloodRequest
            expired_requests = BloodRequest.objects.filter(
                status__in=['expired', 'cancelled'],
                created_at__lt=cutoff_date
            )
            deleted_count = expired_requests.count()
            expired_requests.delete()
            logger.info(f"Cleaned up {deleted_count} expired blood requests")
            
            return {'success': True}
        except Exception as e:
            logger.error(f"Failed to clean up expired data: {e}")
            return {'success': False, 'error': str(e)}
