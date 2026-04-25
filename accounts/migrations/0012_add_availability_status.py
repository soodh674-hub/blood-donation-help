# Generated migration for adding availability_status to User model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0011_add_verification_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='availability_status',
            field=models.CharField(
                choices=[
                    ('available', 'Available to Donate ✅'),
                    ('busy', 'Busy - Currently Donating ⏳'),
                    ('cooldown', 'Cooldown Period (90 days) 🔄'),
                    ('not_available', 'Not Available ❌'),
                ],
                default='available',
                help_text='Current donation availability status',
                max_length=20,
            ),
        ),
    ]
