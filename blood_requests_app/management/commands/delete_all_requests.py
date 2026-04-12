from django.core.management.base import BaseCommand
from blood_requests_app.models import BloodRequest


class Command(BaseCommand):
    help = 'Delete all blood requests from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion of all blood requests',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING('This will DELETE ALL blood requests from the database!')
            )
            self.stdout.write(
                self.style.WARNING('Use --confirm flag to proceed')
            )
            return

        total_count = BloodRequest.objects.count()
        
        if total_count == 0:
            self.stdout.write(self.style.SUCCESS('No blood requests found in database'))
            return

        self.stdout.write(self.style.WARNING(f'Deleting {total_count} blood requests...'))
        
        # Delete all requests
        deleted_count, _ = BloodRequest.objects.all().delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully deleted {deleted_count} blood requests')
        )
