from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from blood_requests_app.models import BloodRequest


class Command(BaseCommand):
    help = 'Update expired blood requests to have future expiration dates'

    def handle(self, *args, **kwargs):
        self.stdout.write('Checking for expired blood requests...')
        
        now = timezone.now()
        expired_requests = BloodRequest.objects.filter(
            status__in=['active', 'approved', 'pending', 'partially_fulfilled'],
            expires_at__lte=now
        )
        
        if expired_requests.count() == 0:
            self.stdout.write(self.style.SUCCESS('No expired requests found!'))
            return
        
        self.stdout.write(f'Found {expired_requests.count()} expired requests to update')
        
        updated_count = 0
        for request in expired_requests:
            # Extend expiration by 7 days from now
            request.expires_at = now + timedelta(days=7)
            request.save(update_fields=['expires_at'])
            updated_count += 1
            
            self.stdout.write(
                f'  ✓ Updated Request #{request.id}: '
                f'{request.patient_blood_group} - {request.hospital_name} '
                f'(New expiry: {request.expires_at.strftime("%Y-%m-%d %H:%M")})'
            )
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Successfully updated {updated_count} blood requests!'
        ))
        self.stdout.write(self.style.WARNING(
            '\n💡 Tip: Create new blood requests with future dates to avoid this issue.'
        ))
