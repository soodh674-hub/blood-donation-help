# Generated migration for profile_photo field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_add_theme_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='donorprofile',
            name='profile_photo',
            field=models.ImageField(
                blank=True,
                help_text='Upload your profile photo',
                null=True,
                upload_to='profile_photos/'
            ),
        ),
    ]
