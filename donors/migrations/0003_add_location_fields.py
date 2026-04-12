# Generated migration for donors app
# Adds location tracking fields to DonorAvailability model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('donors', '0002_donoravailability_last_status_update'),
    ]

    operations = [
        migrations.AddField(
            model_name='donoravailability',
            name='current_latitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='donoravailability',
            name='current_longitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
    ]
