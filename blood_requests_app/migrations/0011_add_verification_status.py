# Generated migration for verification_status field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blood_requests_app', '0010_donorrating_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='bloodrequest',
            name='verification_status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending Verification'),
                    ('verified', 'Verified'),
                    ('rejected', 'Rejected'),
                    ('under_review', 'Under Review')
                ],
                default='pending',
                max_length=20
            ),
        ),
    ]
