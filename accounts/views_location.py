"""
Location autocomplete API using Nominatim (FREE OpenStreetMap)
This provides Swiggy-style location search functionality
"""
import requests
import logging
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
import json

logger = logging.getLogger(__name__)


@require_GET
@csrf_exempt
def location_autocomplete(request):
    """
    Location autocomplete API using Nominatim (FREE)
    Returns location suggestions with lat/lng coordinates
    """
    try:
        query = request.GET.get('q', '').strip()
        
        if not query or len(query) < 3:
            return JsonResponse({
                'success': False,
                'error': 'Query must be at least 3 characters'
            }, status=400)
        
        # Call Nominatim API
        url = settings.NOMINATIM_API_URL
        params = {
            'q': query,
            'format': 'json',
            'addressdetails': 1,
            'limit': 5,
            'countrycodes': 'in',  # India only for better results
        }
        
        headers = {
            'User-Agent': settings.NOMINATIM_USER_AGENT
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        
        # Format results
        results = []
        for item in data:
            address = item.get('address', {})
            display_name = item.get('display_name', '')
            
            # Extract city, state, country
            city = address.get('city') or address.get('town') or address.get('village') or address.get('suburb', '')
            state = address.get('state', '')
            country = address.get('country', '')
            
            results.append({
                'display_name': display_name,
                'lat': float(item.get('lat', 0)),
                'lon': float(item.get('lon', 0)),
                'city': city,
                'state': state,
                'country': country,
                'full_address': display_name
            })
        
        return JsonResponse({
            'success': True,
            'results': results,
            'count': len(results)
        })
        
    except requests.exceptions.Timeout:
        logger.error("Nominatim API timeout")
        return JsonResponse({
            'success': False,
            'error': 'Location service timeout. Please try again.'
        }, status=504)
    except requests.exceptions.RequestException as e:
        logger.error(f"Nominatim API error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Location service unavailable. Please try again.'
        }, status=503)
    except Exception as e:
        logger.error(f"Location autocomplete error: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while fetching locations'
        }, status=500)


@require_GET
@csrf_exempt
def reverse_geocode(request):
    """
    Reverse geocode API: Get address from lat/lng coordinates
    """
    try:
        lat = request.GET.get('lat')
        lon = request.GET.get('lon')
        
        if not lat or not lon:
            return JsonResponse({
                'success': False,
                'error': 'Latitude and longitude are required'
            }, status=400)
        
        # Call Nominatim reverse geocoding API
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            'lat': lat,
            'lon': lon,
            'format': 'json',
            'addressdetails': 1,
        }
        
        headers = {
            'User-Agent': settings.NOMINATIM_USER_AGENT
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        
        address = data.get('address', {})
        
        return JsonResponse({
            'success': True,
            'address': {
                'display_name': data.get('display_name', ''),
                'city': address.get('city') or address.get('town') or address.get('village', ''),
                'state': address.get('state', ''),
                'country': address.get('country', ''),
                'pincode': address.get('postcode', ''),
            }
        })
        
    except Exception as e:
        logger.error(f"Reverse geocode error: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Failed to get address from coordinates'
        }, status=500)
