# Generated migration for donors app
# Adds last_status_update field to DonorAvailability model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('donors', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='donoravailability',
            name='last_status_update',
            field=models.DateField(blank=True, help_text='Last date user updated donation status', null=True),
        ),
    ]
