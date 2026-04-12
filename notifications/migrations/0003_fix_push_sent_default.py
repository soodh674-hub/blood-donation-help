# Generated migration to fix push_sent NOT NULL constraint
# This ensures the database column has the correct default value

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0002_add_category_field'),
    ]

    operations = [
        # Ensure push_sent has a default value in the database
        migrations.AlterField(
            model_name='notification',
            name='push_sent',
            field=models.BooleanField(
                default=False,
                help_text='Whether push notification was sent'
            ),
        ),
    ]
