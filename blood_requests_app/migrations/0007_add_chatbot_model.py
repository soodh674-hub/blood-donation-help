# Generated migration for ChatbotConversation model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_add_settings_models'),
        ('blood_requests_app', '0006_merge_2026'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChatbotConversation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_id', models.CharField(max_length=100, unique=True)),
                ('user_message', models.TextField()),
                ('bot_response', models.TextField()),
                ('confidence', models.CharField(default='medium', max_length=10)),
                ('suggestions', models.JSONField(blank=True, default=list)),
                ('user_context', models.JSONField(blank=True, default=dict)),
                ('is_helpful', models.BooleanField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='chatbot_conversations', to='accounts.user')),
            ],
            options={
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['session_id', 'created_at'], name='blood_reque_session__idx'),
                    models.Index(fields=['user', 'created_at'], name='blood_reque_user__idx'),
                ],
            },
        ),
    ]
