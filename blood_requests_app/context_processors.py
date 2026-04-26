from .models import BloodDonationCamp
from django.utils import timezone


def active_campaign_popup(request):
    """
    Context processor to get the active campaign popup
    Returns the most recent campaign that should be shown as a popup
    """
    campaign = BloodDonationCamp.objects.filter(
        show_as_popup=True,
        status__in=['ongoing', 'upcoming'],
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    ).order_by('-created_at').first()
    
    return {
        'active_campaign_popup': campaign
    }
