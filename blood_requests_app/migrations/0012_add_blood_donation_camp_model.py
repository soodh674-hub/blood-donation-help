# Migration to create BloodDonationCamp model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('blood_requests_app', '0011_add_verification_status'),
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BloodDonationCamp',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True)),
                ('description', models.TextField(blank=True)),
                ('venue', models.CharField(max_length=300)),
                ('address', models.TextField()),
                ('city', models.CharField(max_length=100)),
                ('state', models.CharField(max_length=100)),
                ('start_date', models.DateTimeField()),
                ('end_date', models.DateTimeField()),
                ('status', models.CharField(choices=[('upcoming', 'Upcoming'), ('ongoing', 'Ongoing'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='upcoming', max_length=20)),
                ('target_units', models.IntegerField(default=100)),
                ('collected_units', models.IntegerField(default=0)),
                ('contact_number', models.CharField(max_length=15)),
                ('contact_email', models.EmailField()),
                ('show_as_popup', models.BooleanField(default=False, help_text='Show this campaign as a popup modal on the website')),
                ('banner_image', models.ImageField(blank=True, help_text='Banner image for popup modal', null=True, upload_to='campaign_banners/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organizer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='organized_camps', to='accounts.user')),
            ],
            options={
                'verbose_name': 'Blood Donation Camp',
                'verbose_name_plural': 'Blood Donation Camps',
                'ordering': ['-start_date'],
            },
        ),
    ]
