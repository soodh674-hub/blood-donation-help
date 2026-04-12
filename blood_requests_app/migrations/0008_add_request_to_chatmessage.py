# Migration to add request field to ChatMessage model
# Field is nullable to avoid migration issues

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('blood_requests_app', '0007_add_status_history'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatmessage',
            name='request',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='chat_messages',
                to='blood_requests_app.bloodrequest'
            ),
        ),
    ]
