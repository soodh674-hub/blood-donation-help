from django.utils import timezone
from datetime import timedelta

def smart_banner_context(request):
    """
    Context processor to determine which banner to show based on user status.
    
    Returns:
        dict: Banner configuration including type, message, color, and visibility
    """
    
    # Default: No banner
    context = {
        'show_banner': False,
        'banner_type': None,
        'banner_message': '',
        'banner_color': 'gray',
        'banner_cta_text': '',
        'banner_cta_url': '',
        'banner_dismissible': True,
    }
    
    # Check if user is authenticated
    if not request.user.is_authenticated:
        # Non-logged user: Show welcome banner (once per session)
        has_seen_banner = request.session.get('has_seen_welcome_banner', False)
        
        if not has_seen_banner:
            context.update({
                'show_banner': True,
                'banner_type': 'welcome',
                'banner_message': 'Join our life-saving blood donation community',
                'banner_submessage': 'Connect with hospitals, find donors, and make a difference',
                'banner_color': 'red',
                'banner_cta_text': 'Get Started',
                'banner_cta_url': '/accounts/register/',
                'banner_secondary_cta_text': 'Login',
                'banner_secondary_cta_url': '/accounts/login/',
                'banner_dismissible': True,
            })
        return context
    
    # User is authenticated - check profile completeness
    user = request.user
    
    # Calculate profile completeness percentage
    completeness_score = 0
    missing_fields = []
    
    # Check blood group
    if user.blood_group:
        completeness_score += 20
    else:
        missing_fields.append('blood_group')
    
    # Check phone number
    if user.phone_number:
        completeness_score += 20
    else:
        missing_fields.append('phone_number')
    
    # Check last donation date
    if user.last_donation_date:
        completeness_score += 20
    else:
        missing_fields.append('last_donation_date')
    
    # Check availability status
    if hasattr(user, 'is_available'):
        completeness_score += 20
    else:
        missing_fields.append('availability_status')
    
    # Check location (city/state)
    if user.city or user.state:
        completeness_score += 20
    else:
        missing_fields.append('location')
    
    context['profile_completeness'] = completeness_score
    context['missing_fields'] = missing_fields
    
    # Priority 1: Profile incomplete (less than 100%)
    if completeness_score < 100 and len(missing_fields) > 0:
        # Create friendly message based on what's missing
        if 'last_donation_date' in missing_fields:
            message = "⚠️ Please update your last donation date to help others track eligibility"
        elif 'phone_number' in missing_fields:
            message = "⚠️ Add your phone number so hospitals can contact you quickly"
        elif 'blood_group' in missing_fields:
            message = "⚠️ Please add your blood group for faster matching"
        else:
            message = f"⚠️ Complete your profile ({completeness_score}%) to maximize your impact"
        
        context.update({
            'show_banner': True,
            'banner_type': 'profile_update',
            'banner_message': message,
            'banner_submessage': f'Missing: {", ".join(missing_fields[:3])}' if len(missing_fields) <= 3 else f'Missing: {", ".join(missing_fields[:2])} +{len(missing_fields) - 2} more',
            'banner_color': 'orange',
            'banner_cta_text': 'Update Profile',
            'banner_cta_url': '/accounts/profile/',
            'banner_dismissible': True,
        })
        return context
    
    # Priority 2: Check donation eligibility (if last donation date exists)
    if user.last_donation_date:
        days_since_donation = (timezone.now().date() - user.last_donation_date).days
        days_until_eligible = 90 - days_since_donation
        
        # Store eligibility info for other parts of the site
        context['days_since_donation'] = days_since_donation
        context['days_until_eligible'] = max(0, days_until_eligible)
        context['is_eligible_now'] = days_since_donation >= 90
        
        if days_since_donation >= 90 and user.is_available:
            # User is eligible to donate again!
            context.update({
                'show_banner': True,
                'banner_type': 'eligibility_reminder',
                'banner_message': '✅ You\'re eligible to donate blood again!',
                'banner_submessage': f'It\'s been {days_since_donation} days since your last donation. Ready to save lives?',
                'banner_color': 'green',
                'banner_cta_text': 'Update Availability',
                'banner_cta_url': '/accounts/profile/',
                'banner_dismissible': True,
            })
            return context
        elif days_since_donation >= 60 and days_since_donation < 90:
            # Coming up soon - gentle reminder
            context.update({
                'show_banner': True,
                'banner_type': 'upcoming_eligibility',
                'banner_message': f'📅 You\'ll be eligible to donate in {days_until_eligible} days',
                'banner_submessage': 'Mark your calendar and prepare to make a difference!',
                'banner_color': 'blue',
                'banner_cta_text': 'Set Reminder',
                'banner_cta_url': '/notifications/',
                'banner_dismissible': True,
            })
            return context
    
    # Priority 3: If donor but not marked as available
    if user.user_type == 'donor' and not user.is_available:
        context.update({
            'show_banner': True,
            'banner_type': 'availability_reminder',
            'banner_message': '💡 Mark yourself as available when you can donate',
            'banner_submessage': 'This helps hospitals find you quickly in emergencies',
            'banner_color': 'yellow',
            'banner_cta_text': 'Update Status',
            'banner_cta_url': '/accounts/profile/',
            'banner_dismissible': True,
        })
        return context
    
    # No banner needed - user is all set!
    return context


def notification_count_context(request):
    """
    Context processor to add unread notification count for navbar.
    """
    if request.user.is_authenticated:
        try:
            from notifications.models import Notification
            unread_count = Notification.objects.filter(
                user=request.user,
                is_read=False
            ).count()
            return {'unread_notification_count': unread_count}
        except Exception:
            pass
    return {'unread_notification_count': 0}
