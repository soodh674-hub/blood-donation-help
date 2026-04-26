# Generated migration for campaign popup fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blood_requests_app', '0012_add_blood_donation_camp_model'),
    ]

    operations = [
        # This migration is now a no-op since the fields are already included in 0012
        # Kept for migration history consistency
        migrations.RunSQL(sql="-- No-op migration", reverse_sql="-- No-op migration"),
    ]
