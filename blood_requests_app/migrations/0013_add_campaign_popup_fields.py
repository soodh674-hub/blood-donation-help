# Generated migration for campaign popup fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blood_requests_app', '0011_add_verification_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='blooddonationcamp',
            name='show_as_popup',
            field=models.BooleanField(default=False, help_text='Show this campaign as a popup modal on the website'),
        ),
        migrations.AddField(
            model_name='blooddonationcamp',
            name='banner_image',
            field=models.ImageField(blank=True, help_text='Banner image for popup modal', null=True, upload_to='campaign_banners/'),
        ),
    ]
