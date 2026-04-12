# Generated merge migration to resolve conflict between 0004 and 0005

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blood_requests_app', '0004_add_chat_models'),
        ('blood_requests_app', '0005_add_tracking_fields'),
    ]

    operations = [
        # This is a merge migration - no operations needed
        # It simply declares that both 0004 and 0005 must be applied
        # before any subsequent migrations
    ]
