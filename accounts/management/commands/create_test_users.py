from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Create a test user for login testing'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Check if test user already exists
        if User.objects.filter(username='testuser').exists():
            self.stdout.write(self.style.WARNING('Test user already exists'))
            test_user = User.objects.get(username='testuser')
        else:
            # Create test user
            test_user = User.objects.create_user(
                username='testuser',
                email='test@example.com',
                password='Testpass123!',
                first_name='Test',
                last_name='User',
                user_type='donor',
                is_active=True,
                is_verified=True
            )
            self.stdout.write(self.style.SUCCESS('Created test user: testuser / Testpass123!'))
        
        # Also create admin user if it doesn't exist
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123'
            )
            self.stdout.write(self.style.SUCCESS('Created admin user: admin / admin123'))
        else:
            self.stdout.write(self.style.SUCCESS('Admin user already exists'))
        
        self.stdout.write(f'\nAvailable users:')
        self.stdout.write(f'- testuser / Testpass123!')
        self.stdout.write(f'- admin / admin123')