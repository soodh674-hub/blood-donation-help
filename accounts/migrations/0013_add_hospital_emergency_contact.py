# Generated migration to add emergency_contact field to Hospital model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0012_add_hospital_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='hospital',
            name='emergency_contact',
            field=models.CharField(max_length=15, blank=True),
        ),
    ]
