from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Create default superuser if it does not exist'

    def handle(self, *args, **options):
        self.stdout.write("=== CHECKING SUPERUSER ===")
        
        try:
            User = get_user_model()
            
            # Create superuser if needed
            if not User.objects.filter(is_superuser=True).exists():
                self.stdout.write("Creating default superuser...")
                User.objects.create_superuser(
                    username='admin',
                    email='admin@example.com',
                    password='admin123'
                )
                self.stdout.write(self.style.SUCCESS("✓ Superuser created: admin/admin123"))
            else:
                self.stdout.write(self.style.SUCCESS("✓ Superuser already exists"))
                
            # Verify everything works
            user_count = User.objects.count()
            self.stdout.write(self.style.SUCCESS(f"✓ Database check complete - {user_count} users in database"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Database check failed: {e}"))
            logger.error(f"Database check error: {e}", exc_info=True)
            
        self.stdout.write("=== DATABASE CHECK COMPLETE ===")