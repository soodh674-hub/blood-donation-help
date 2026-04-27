"""
Management command to auto-approve pending blood requests based on priority rules
"""
from django.core.management.base import BaseCommand
from blood_requests_app.services import AutoApprovalService
from blood_requests_app.models import BloodRequest


class Command(BaseCommand):
    help = 'Auto-approve pending blood requests based on priority rules'
    
    def handle(self, *args, **kwargs):
        self.stdout.write('Checking for pending requests to auto-approve...')
        
        pending_requests = BloodRequest.objects.filter(status='pending')
        approved_count = 0
        skipped_count = 0
        
        for request in pending_requests:
            try:
                if AutoApprovalService.check_and_approve(request):
                    approved_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Auto-approved request #{request.id} ({request.priority} priority)')
                    )
                else:
                    skipped_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error processing request #{request.id}: {str(e)}')
                )
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Auto-approval complete!'))
        self.stdout.write(f'  Approved: {approved_count}')
        self.stdout.write(f'  Skipped: {skipped_count}')
        self.stdout.write(f'  Total checked: {pending_requests.count()}\n')
