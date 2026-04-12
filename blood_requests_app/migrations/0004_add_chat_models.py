# Generated migration for chat functionality

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('blood_requests_app', '0003_add_realtime_tracking'),
    ]

    operations = [
        # ChatMessage model
        migrations.CreateModel(
            name='ChatMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField()),
                ('message_type', models.CharField(choices=[('text', 'Text Message'), ('system', 'System Message'), ('emergency', 'Emergency Alert')], default='text', max_length=10)),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_messages', to=settings.AUTH_USER_MODEL)),
                ('receiver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_messages', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        
        # ChatRoom model
        migrations.CreateModel(
            name='ChatRoom',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('room_type', models.CharField(choices=[('request', 'Request-specific Room'), ('emergency', 'Emergency Alert Room'), ('general', 'General Discussion')], default='request', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
                ('blood_request', models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.CASCADE, to='blood_requests_app.bloodrequest')),
                ('participants', models.ManyToManyField(related_name='chat_rooms', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        
        # RoomMessage model
        migrations.CreateModel(
            name='RoomMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='blood_requests_app.chatroom')),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        
        # NotificationMessage model
        migrations.CreateModel(
            name='NotificationMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_type', models.CharField(choices=[('new_request', 'New Blood Request'), ('donor_response', 'Donor Response'), ('request_fulfilled', 'Request Fulfilled'), ('emergency_alert', 'Emergency Alert'), ('chat_message', 'New Chat Message')], max_length=20)),
                ('priority', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent'), ('emergency', 'Emergency')], default='medium', max_length=10)),
                ('title', models.CharField(max_length=200)),
                ('message', models.TextField()),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL)),
                ('related_request', models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.CASCADE, to='blood_requests_app.bloodrequest')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        
        # UserLocation model
        migrations.CreateModel(
            name='UserLocation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('latitude', models.DecimalField(decimal_places=8, max_digits=10)),
                ('longitude', models.DecimalField(decimal_places=8, max_digits=11)),
                ('accuracy', models.FloatField(null=True, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='locations', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        
        # TypingIndicator model
        migrations.CreateModel(
            name='TypingIndicator',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_typing', models.BooleanField(default=True)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('room', models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.CASCADE, to='blood_requests_app.chatroom')),
                ('receiver', models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='typing_indicators', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        
        # Note: Indexes will be added separately due to Django version compatibility
    ]
