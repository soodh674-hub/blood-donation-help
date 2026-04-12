# Generated migration to fix profile_visibility max_length

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_add_settings_models'),
    ]

    operations = [
        migrations.AlterField(
            model_name='privacysettings',
            name='profile_visibility',
            field=models.CharField(
                choices=[
                    ('public', 'Public - Everyone can see'),
                    ('donors_only', 'Donors Only'),
                    ('private', 'Private - Hidden'),
                ],
                default='public',
                max_length=30,
            ),
        ),
    ]
