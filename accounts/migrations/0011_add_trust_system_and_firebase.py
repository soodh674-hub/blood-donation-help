# Generated migration manually for trust system and Firebase integration
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0010_add_profile_completion_tracking'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='trust_score',
            field=models.IntegerField(default=50, help_text='User trust score (0-100) based on donations and reports'),
        ),
        migrations.AddField(
            model_name='user',
            name='reports_count',
            field=models.IntegerField(default=0, help_text='Number of times this user has been reported'),
        ),
        migrations.AddField(
            model_name='user',
            name='donations_completed',
            field=models.IntegerField(default=0, help_text='Number of successful blood donations'),
        ),
        migrations.AddField(
            model_name='user',
            name='is_blocked',
            field=models.BooleanField(default=False, help_text='Whether user is blocked due to multiple reports'),
        ),
        migrations.AddField(
            model_name='user',
            name='firebase_uid',
            field=models.CharField(max_length=100, null=True, blank=True, help_text='Firebase user ID for authentication'),
        ),
        migrations.AddField(
            model_name='user',
            name='fcm_token',
            field=models.CharField(max_length=255, null=True, blank=True, help_text='Firebase Cloud Messaging token for push notifications'),
        ),
    ]
