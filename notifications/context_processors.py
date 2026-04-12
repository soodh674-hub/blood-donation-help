"""
Context processors for notifications and donation reminders
"""
from datetime import date
from django.utils import timezone
from donors.models import DonorAvailability


def donation_status_popup(request):
    """
    Context processor to check if we should show donation status update popup
    
    Returns:
        dict with popup visibility and eligibility info
    """
    context = {
        'show_donation_popup': False,
        'popup_message': '',
        'is_eligible': False,
        'days_until_eligible': None,
    }
    
    # Only for authenticated users
    if not request.user.is_authenticated:
        return context
    
    try:
        # Get or create donor availability profile
        availability, created = DonorAvailability.objects.get_or_create(
            donor=request.user,
            defaults={'is_available': True}
        )
        
        # Check if user updated status today
        if availability.last_status_update == date.today():
            # Already updated today, don't show popup
            context['show_donation_popup'] = False
            return context
        
        # User hasn't updated today, check eligibility
        from notifications.models import DonationReminderManager
        
        eligibility = DonationReminderManager.check_eligibility(request.user)
        
        context['show_donation_popup'] = True
        context['is_eligible'] = eligibility['eligible']
        context['days_until_eligible'] = eligibility['days_until_eligible']
        context['popup_message'] = eligibility['message']
        
        # Customize message based on eligibility
        if eligibility['eligible']:
            context['popup_title'] = "Time to Update Your Status! ❤️"
            context['popup_type'] = "success"
        else:
            context['popup_title'] = "Donation Status Reminder"
            context['popup_type'] = "info"
        
    except Exception as e:
        # If anything fails, just don't show popup
        context['show_donation_popup'] = False
    
    return context
