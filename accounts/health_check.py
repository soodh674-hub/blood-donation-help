from django.http import JsonResponse
from django.db import connection
from django.views.decorators.csrf import csrf_exempt


def health_check(request):
    """Health check endpoint to test database connectivity"""
    try:
        # Test database connection
        connection.ensure_connection()
        db_status = "OK"
    except Exception as e:
        db_status = f"ERROR: {str(e)}"
    
    return JsonResponse({
        "status": "healthy" if db_status == "OK" else "unhealthy",
        "database": db_status,
        "service": "blood-donation-platform"
    })