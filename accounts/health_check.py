from django.http import JsonResponse
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import time
import logging

logger = logging.getLogger(__name__)


@csrf_exempt
def health_check(request):
    """Enhanced health check endpoint with comprehensive system status"""
    health_status = {
        'status': 'healthy',
        'timestamp': time.time(),
        'version': '2.0.0',
        'checks': {}
    }
    
    # Database check
    try:
        start_time = time.time()
        connection.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        db_time = round((time.time() - start_time) * 1000, 2)
        health_status['checks']['database'] = {
            'status': 'ok',
            'response_time_ms': db_time
        }
    except Exception as e:
        health_status['checks']['database'] = {
            'status': 'error',
            'error': str(e)
        }
        health_status['status'] = 'degraded'
        logger.error(f"Database health check failed: {e}")
    
    # Redis/Cache check
    try:
        from django.core.cache import cache
        start_time = time.time()
        cache.set('health_check', 'ok', 10)
        result = cache.get('health_check')
        cache_time = round((time.time() - start_time) * 1000, 2)
        
        if result == 'ok':
            health_status['checks']['cache'] = {
                'status': 'ok',
                'response_time_ms': cache_time
            }
        else:
            raise Exception('Cache returned unexpected result')
    except Exception as e:
        health_status['checks']['cache'] = {
            'status': 'warning',
            'error': str(e)
        }
        logger.warning(f"Cache health check failed: {e}")
    
    # Email configuration check
    try:
        email_backend = getattr(settings, 'EMAIL_BACKEND', '')
        if 'BrevoAPI' in email_backend:
            api_key = getattr(settings, 'BREVO_API_KEY', '')
            if api_key and len(api_key) > 10:
                health_status['checks']['email'] = {
                    'status': 'ok',
                    'backend': 'Brevo API'
                }
            else:
                health_status['checks']['email'] = {
                    'status': 'warning',
                    'message': 'Brevo API key not configured'
                }
        else:
            health_status['checks']['email'] = {
                'status': 'ok',
                'backend': email_backend.split('.')[-1]
            }
    except Exception as e:
        health_status['checks']['email'] = {
            'status': 'warning',
            'error': str(e)
        }
    
    # Overall status determination
    critical_failures = any(
        check.get('status') == 'error' 
        for check_name, check in health_status['checks'].items()
        if check_name in ['database']
    )
    
    if critical_failures:
        health_status['status'] = 'unhealthy'
        return JsonResponse(health_status, status=503)
    
    has_warnings = any(
        check.get('status') in ['warning', 'error']
        for check in health_status['checks'].values()
    )
    
    if has_warnings:
        health_status['status'] = 'degraded'
        return JsonResponse(health_status, status=200)
    
    return JsonResponse(health_status, status=200)