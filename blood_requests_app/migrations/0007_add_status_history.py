# Migration to add status_history JSONField to BloodRequest model
# This field tracks all status changes with timestamps

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blood_requests_app', '0006_merge_2026'),
    ]

    operations = [
        migrations.AddField(
            model_name='bloodrequest',
            name='status_history',
            field=models.JSONField(blank=True, default=list, help_text='Track all status changes with timestamps'),
        ),
    ]
