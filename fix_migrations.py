import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blood_donation.settings')
django.setup()

from django.db import connection

print("Fixing migration history...")

cursor = connection.cursor()

# Delete problematic migration records
cursor.execute("DELETE FROM django_migrations WHERE app IN ('notifications', 'blood_requests_app')")
deleted_count = cursor.rowcount

print(f"Deleted {deleted_count} migration records")
print("Migration history cleared for notifications and blood_requests_app")
print("\nNow you can run: python manage.py migrate")
