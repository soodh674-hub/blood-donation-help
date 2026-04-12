# Generated migration to add real-time tracking models and fields
# Added: RequestResponse, DonorLocationHistory models
# Updated BloodRequest with tracking fields

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('blood_requests_app', '0002_add_exact_address'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Create RequestResponse model
        migrations.CreateModel(
            name='RequestResponse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('interested', 'Interested - Will Donate'), ('en_route', 'En Route to Hospital'), ('arrived', 'Arrived at Hospital'), ('donated', 'Donation Completed'), ('unavailable', 'No Longer Available'), ('declined', 'Declined')], default='interested', max_length=15)),
                ('responded_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('en_route_at', models.DateTimeField(blank=True, null=True)),
                ('arrived_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('donor_latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('donor_longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('last_location_update', models.DateTimeField(blank=True, null=True)),
                ('distance_km', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ('estimated_arrival_minutes', models.IntegerField(blank=True, null=True)),
                ('is_selected', models.BooleanField(default=False, help_text='Selected by requester')),
                ('selected_at', models.DateTimeField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
                ('donor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='request_responses', to=settings.AUTH_USER_MODEL)),
                ('request', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='responses', to='blood_requests_app.bloodrequest')),
            ],
            options={
                'ordering': ['-responded_at'],
                'unique_together': {('request', 'donor')},
            },
        ),
        
        # Create DonorLocationHistory model
        migrations.CreateModel(
            name='DonorLocationHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('latitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('longitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('accuracy_meters', models.FloatField(blank=True, null=True, help_text='GPS accuracy in meters')),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('donor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='location_history', to=settings.AUTH_USER_MODEL)),
                ('request', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='location_tracking', to='blood_requests_app.bloodrequest')),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
        
        # Add indexes for RequestResponse
        migrations.AddIndex(
            model_name='requestresponse',
            index=models.Index(fields=['status'], name='blood_reque_status_abc123_idx'),
        ),
        migrations.AddIndex(
            model_name='requestresponse',
            index=models.Index(fields=['is_selected'], name='blood_reque_is_sele_def456_idx'),
        ),
        
        # Add indexes for DonorLocationHistory
        migrations.AddIndex(
            model_name='donorlocationhistory',
            index=models.Index(fields=['donor', 'timestamp'], name='blood_reque_donor_i_ghi789_idx'),
        ),
    ]
