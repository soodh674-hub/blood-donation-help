from django.core.management.base import BaseCommand
from django.db import connection
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Check database setup and run necessary migrations'

    def handle(self, *args, **options):
        self.stdout.write("Checking database setup...")
        
        # Check if tables exist
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
        self.stdout.write(f"Found {len(tables)} tables in database:")
        for table in tables:
            self.stdout.write(f"  - {table}")
        
        # Check specifically for accounts_user
        if 'accounts_user' in tables:
            self.stdout.write(self.style.SUCCESS("✓ accounts_user table exists"))
        else:
            self.stdout.write(self.style.ERROR("✗ accounts_user table missing"))
            
        # Check for auth_user (Django's default)
        if 'auth_user' in tables:
            self.stdout.write(self.style.WARNING("⚠ auth_user table exists (may conflict)"))
        else:
            self.stdout.write("✓ No conflicting auth_user table")
            
        # Try to access the User model
        try:
            User = get_user_model()
            user_count = User.objects.count()
            self.stdout.write(self.style.SUCCESS(f"✓ User model accessible, {user_count} users in database"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ User model error: {e}"))
            
        self.stdout.write("Database check complete.")