"""
Trust-based feature restrictions
Users with low trust scores are restricted from certain features
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse


def check_trust_score(min_score=50):
    """
    Decorator to check if user has minimum trust score to access a feature
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                # Check if it's an API view (returns JSON)
                if hasattr(view_func, '__name__') and 'api' in view_func.__name__.lower():
                    return JsonResponse({'success': False, 'message': 'Please login first'}, status=401)
                return redirect('/accounts/login/?next=' + request.path)
            
            # Check if user is blocked
            if getattr(request.user, 'is_blocked', False):
                if hasattr(view_func, '__name__') and 'api' in view_func.__name__.lower():
                    return JsonResponse({'success': False, 'message': 'Your account has been blocked due to multiple reports. Contact support for assistance.'}, status=403)
                messages.error(request, 'Your account has been blocked due to multiple reports. Contact support for assistance.')
                return redirect('/')
            
            # Check trust score
            user_trust_score = getattr(request.user, 'trust_score', 50)
            
            if user_trust_score < min_score:
                if hasattr(view_func, '__name__') and 'api' in view_func.__name__.lower():
                    return JsonResponse({
                        'success': False,
                        'message': f'Your trust score ({user_trust_score}%) is too low for this feature. Minimum required: {min_score}%. Complete successful donations to improve your score.'
                    }, status=403)
                messages.warning(
                    request, 
                    f'Your trust score ({user_trust_score}%) is too low for this feature. '
                    f'Minimum required: {min_score}%. Complete successful donations to improve your score.'
                )
                return redirect('/')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def check_not_blocked(view_func):
    """
    Decorator to check if user is not blocked
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if hasattr(view_func, '__name__') and 'api' in view_func.__name__.lower():
                return JsonResponse({'success': False, 'message': 'Please login first'}, status=401)
            return redirect('/accounts/login/?next=' + request.path)
        
        if getattr(request.user, 'is_blocked', False):
            if hasattr(view_func, '__name__') and 'api' in view_func.__name__.lower():
                return JsonResponse({'success': False, 'message': 'Your account has been blocked due to multiple reports. Contact support for assistance.'}, status=403)
            messages.error(request, 'Your account has been blocked due to multiple reports. Contact support for assistance.')
            return redirect('/')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def check_donation_eligibility(view_func):
    """
    Decorator to check if user is eligible to donate (trust score >= 40)
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if hasattr(view_func, '__name__') and 'api' in view_func.__name__.lower():
                return JsonResponse({'success': False, 'message': 'Please login first'}, status=401)
            return redirect('/accounts/login/?next=' + request.path)
        
        if getattr(request.user, 'is_blocked', False):
            if hasattr(view_func, '__name__') and 'api' in view_func.__name__.lower():
                return JsonResponse({'success': False, 'message': 'Your account has been blocked due to multiple reports. Contact support for assistance.'}, status=403)
            messages.error(request, 'Your account has been blocked due to multiple reports. Contact support for assistance.')
            return redirect('/')
        
        user_trust_score = getattr(request.user, 'trust_score', 50)
        
        if user_trust_score < 40:
            if hasattr(view_func, '__name__') and 'api' in view_func.__name__.lower():
                return JsonResponse({
                    'success': False,
                    'message': f'Your trust score ({user_trust_score}%) is too low to donate blood. Minimum required: 40%. Complete profile verification to improve your score.'
                }, status=403)
            messages.warning(
                request, 
                f'Your trust score ({user_trust_score}%) is too low to donate blood. '
                f'Minimum required: 40%. Complete profile verification to improve your score.'
            )
            return redirect('/')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def check_request_eligibility(view_func):
    """
    Decorator to check if user is eligible to create blood requests (trust score >= 30)
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if hasattr(view_func, '__name__') and 'api' in view_func.__name__.lower():
                return JsonResponse({'success': False, 'message': 'Please login first'}, status=401)
            return redirect('/accounts/login/?next=' + request.path)
        
        if getattr(request.user, 'is_blocked', False):
            if hasattr(view_func, '__name__') and 'api' in view_func.__name__.lower():
                return JsonResponse({'success': False, 'message': 'Your account has been blocked due to multiple reports. Contact support for assistance.'}, status=403)
            messages.error(request, 'Your account has been blocked due to multiple reports. Contact support for assistance.')
            return redirect('/')
        
        user_trust_score = getattr(request.user, 'trust_score', 50)
        
        if user_trust_score < 30:
            if hasattr(view_func, '__name__') and 'api' in view_func.__name__.lower():
                return JsonResponse({
                    'success': False,
                    'message': f'Your trust score ({user_trust_score}%) is too low to create blood requests. Minimum required: 30%. Complete profile verification to improve your score.'
                }, status=403)
            messages.warning(
                request, 
                f'Your trust score ({user_trust_score}%) is too low to create blood requests. '
                f'Minimum required: 30%. Complete profile verification to improve your score.'
            )
            return redirect('/')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view
