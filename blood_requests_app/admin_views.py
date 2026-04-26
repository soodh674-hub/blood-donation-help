from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from accounts.models import User
from blood_requests_app.models import BloodRequest, BloodDonationCamp


@staff_member_required
def custom_admin_index(request):
    """
    Custom admin dashboard with statistics and quick actions
    """
    # Calculate statistics
    total_users = User.objects.count()
    total_requests = BloodRequest.objects.count()
    pending_requests = BloodRequest.objects.filter(status='pending').count()
    total_camps = BloodDonationCamp.objects.filter(status__in=['ongoing', 'upcoming']).count()
    
    context = {
        'total_users': total_users,
        'total_requests': total_requests,
        'pending_requests': pending_requests,
        'total_camps': total_camps,
    }
    
    return render(request, 'admin/index.html', context)
