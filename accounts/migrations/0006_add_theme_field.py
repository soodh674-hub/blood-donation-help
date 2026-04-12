# Generated migration for adding theme field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_fix_profile_visibility_length'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='theme',
            field=models.CharField(
                max_length=10,
                choices=[('dark', 'Dark Mode'), ('light', 'Light Mode')],
                default='dark'
            ),
        ),
    ]
