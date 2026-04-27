# Generated migration to add missing Hospital model fields
# These fields were added to the model but migration was not created

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0015_fix_cascade_delete'),
    ]

    operations = [
        # Add blood bank details
        migrations.AddField(
            model_name='hospital',
            name='has_blood_bank',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='hospital',
            name='blood_groups_available',
            field=models.JSONField(default=list, help_text='List of available blood groups'),
        ),
        
        # Add verification fields
        migrations.AddField(
            model_name='hospital',
            name='verified_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='verified_hospitals',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='hospital',
            name='verified_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='hospital',
            name='verification_documents',
            field=models.FileField(blank=True, null=True, upload_to='hospital_documents/'),
        ),
        
        # Add statistics fields
        migrations.AddField(
            model_name='hospital',
            name='total_donations_processed',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='hospital',
            name='active_requests',
            field=models.IntegerField(default=0),
        ),
        
        # Add trust score field
        migrations.AddField(
            model_name='hospital',
            name='trust_score',
            field=models.IntegerField(default=50, help_text='Trust score from 0-100'),
        ),
        
        # Remove old is_active field if it exists (replaced by verification_status)
        migrations.RemoveField(
            model_name='hospital',
            name='is_active',
        ),
        
        # Add indexes for better query performance
        migrations.AddIndex(
            model_name='hospital',
            index=models.Index(fields=['city', 'verification_status'], name='accounts_ho_city_abc123_idx'),
        ),
        migrations.AddIndex(
            model_name='hospital',
            index=models.Index(fields=['trust_score'], name='accounts_ho_trust_s_def456_idx'),
        ),
    ]
