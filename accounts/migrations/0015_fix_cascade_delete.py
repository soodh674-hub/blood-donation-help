# Generated migration to fix CASCADE delete issues
from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0014_add_loginotp_model'),
    ]

    operations = [
        # Create UserReport model if it doesn't exist
        migrations.CreateModel(
            name='UserReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reason', models.CharField(choices=[('fake_profile', 'Fake Profile'), ('spam', 'Spam Messages'), ('inappropriate', 'Inappropriate Behavior'), ('scam', 'Scam Attempt'), ('harassment', 'Harassment'), ('other', 'Other')], max_length=50)),
                ('description', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('pending', 'Pending Review'), ('investigating', 'Under Investigation'), ('resolved', 'Resolved'), ('dismissed', 'Dismissed')], default='pending', max_length=20)),
                ('is_resolved', models.BooleanField(default=False)),
                ('admin_notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('reporter', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reports_made', to=settings.AUTH_USER_MODEL)),
                ('reported_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reports_received', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('reporter', 'reported_user')},
                'ordering': ['-created_at'],
            },
        ),
        # Create DonorRating model if it doesn't exist
        migrations.CreateModel(
            name='DonorRating',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.IntegerField(choices=[(1, 'Poor'), (2, 'Fair'), (3, 'Good'), (4, 'Very Good'), (5, 'Excellent')])),
                ('review', models.TextField(blank=True, help_text='Optional review/comments')),
                ('punctuality', models.IntegerField(choices=[(1, 'Poor'), (2, 'Fair'), (3, 'Good'), (4, 'Very Good'), (5, 'Excellent')], default=5, help_text='Arrived on time')),
                ('professionalism', models.IntegerField(choices=[(1, 'Poor'), (2, 'Fair'), (3, 'Good'), (4, 'Very Good'), (5, 'Excellent')], default=5, help_text='Professional behavior')),
                ('communication', models.IntegerField(choices=[(1, 'Poor'), (2, 'Fair'), (3, 'Good'), (4, 'Very Good'), (5, 'Excellent')], default=5, help_text='Communication quality')),
                ('is_verified', models.BooleanField(default=False, help_text='Verified by hospital staff')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('donor', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='accounts_received_ratings', to=settings.AUTH_USER_MODEL)),
                ('rater', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='accounts_given_ratings', to=settings.AUTH_USER_MODEL)),
                ('blood_request', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='accounts_ratings', to='blood_requests_app.bloodrequest')),
                ('verified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='verified_ratings', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
