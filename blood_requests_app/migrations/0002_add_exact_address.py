# Generated migration to add missing fields to BloodRequest model
# Added: exact_address, max_donors, auto_expire_hours, tracking_enabled, activated_at

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blood_requests_app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='bloodrequest',
            name='exact_address',
            field=models.TextField(blank=True, help_text='Detailed address for navigation'),
        ),
        migrations.AddField(
            model_name='bloodrequest',
            name='max_donors',
            field=models.IntegerField(default=5, help_text='Maximum donors that can respond'),
        ),
        migrations.AddField(
            model_name='bloodrequest',
            name='auto_expire_hours',
            field=models.IntegerField(default=6, help_text='Auto-expire after X hours'),
        ),
        migrations.AddField(
            model_name='bloodrequest',
            name='tracking_enabled',
            field=models.BooleanField(default=True, help_text='Enable live donor tracking'),
        ),
        migrations.AddField(
            model_name='bloodrequest',
            name='activated_at',
            field=models.DateTimeField(blank=True, null=True, help_text='When request went live'),
        ),
        migrations.AddIndex(
            model_name='bloodrequest',
            index=models.Index(fields=['latitude', 'longitude'], name='blood_reque_latitud_12345_idx'),
        ),
    ]
