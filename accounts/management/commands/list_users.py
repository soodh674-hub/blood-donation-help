from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'List all users in the system'

    def handle(self, *args, **options):
        User = get_user_model()
        users = User.objects.all()
        
        if users.count() == 0:
            self.stdout.write("No users found in the database.")
        else:
            self.stdout.write(f"Found {users.count()} user(s):\n")
            for user in users:
                status = "ACTIVE" if user.is_active else "INACTIVE"
                superuser = " (SUPERUSER)" if user.is_superuser else ""
                self.stdout.write(f"- {user.username} ({user.email}) [{status}]{superuser}")

        # Also check for any registration issues
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM accounts_user;")
            count = cursor.fetchone()[0]
            self.stdout.write(f"\nDirect database check - accounts_user table has {count} records")