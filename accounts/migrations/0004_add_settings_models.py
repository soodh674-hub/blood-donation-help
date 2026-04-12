# Generated manually for settings panel models

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_passwordresetotp'),
    ]

    operations = [
        # Create NotificationSettings model
        migrations.CreateModel(
            name='NotificationSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('blood_request_alerts', models.BooleanField(default=True)),
                ('emergency_alerts', models.BooleanField(default=True)),
                ('nearby_donation_requests', models.BooleanField(default=True)),
                ('donation_reminders', models.BooleanField(default=True)),
                ('chat_notifications', models.BooleanField(default=True)),
                ('system_updates', models.BooleanField(default=True)),
                ('email_notifications', models.BooleanField(default=True)),
                ('sms_notifications', models.BooleanField(default=False)),
                ('push_notifications', models.BooleanField(default=True)),
                ('quiet_hours_enabled', models.BooleanField(default=False)),
                ('quiet_hours_start', models.TimeField(default='23:00:00')),
                ('quiet_hours_end', models.TimeField(default='06:00:00')),
                ('search_radius_km', models.IntegerField(choices=[(5, '5 km'), (10, '10 km'), (25, '25 km'), (50, '50 km'), (100, '100 km')], default=25)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='notification_settings', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        
        # Create PrivacySettings model
        migrations.CreateModel(
            name='PrivacySettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('profile_visibility', models.CharField(choices=[('public', 'Public'), ('donors_only', 'Donors Only'), ('private', 'Private')], default='public', max_length=20)),
                ('show_email', models.BooleanField(default=False)),
                ('show_phone', models.BooleanField(default=False)),
                ('show_location', models.BooleanField(default=True)),
                ('anonymous_mode', models.BooleanField(default=False)),
                ('allow_messages', models.BooleanField(default=True)),
                ('data_sharing_consent', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='privacy_settings', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        
        # Create DonorProfile model
        migrations.CreateModel(
            name='DonorProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_available', models.BooleanField(default=True)),
                ('last_donation_date', models.DateField(blank=True, null=True)),
                ('next_eligible_date', models.DateField(blank=True, null=True)),
                ('total_donations', models.IntegerField(default=0)),
                ('preferred_locations', models.JSONField(blank=True, default=list)),
                ('emergency_contact_name', models.CharField(blank=True, max_length=200)),
                ('emergency_contact_phone', models.CharField(blank=True, max_length=15)),
                ('emergency_contact_relation', models.CharField(blank=True, max_length=100)),
                ('medical_conditions', models.TextField(blank=True)),
                ('medications', models.TextField(blank=True)),
                ('allergies', models.TextField(blank=True)),
                ('availability_schedule', models.JSONField(blank=True, default=dict)),
                ('auto_accept_emergency', models.BooleanField(default=False)),
                ('max_distance_km', models.IntegerField(default=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='donor_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        
        # Create UserActivityLog model
        migrations.CreateModel(
            name='UserActivityLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=100)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('details', models.JSONField(blank=True, default=dict)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activity_logs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-timestamp'],
                'indexes': [models.Index(fields=['user', '-timestamp'], name='accounts_us_user_id_abc123_idx')],
            },
        ),
    ]
