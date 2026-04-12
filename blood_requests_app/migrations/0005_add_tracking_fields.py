# Generated migration to add missing tracking fields to BloodRequest
# NOTE: This migration has been converted to a no-op because the fields
# already exist in the database from a previous deployment/schema change.

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blood_requests_app', '0003_add_realtime_tracking'),
    ]

    operations = [
        # Fields already exist in database - skip adding them
        # This migration is kept for dependency chain integrity
        migrations.RunSQL(
            sql="SELECT 1",  # No-op SQL
            reverse_sql="SELECT 1",
        ),
    ]
