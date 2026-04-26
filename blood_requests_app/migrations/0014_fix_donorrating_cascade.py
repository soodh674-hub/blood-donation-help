# Generated migration to fix DonorRating cascade delete issues

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('blood_requests_app', '0013_add_campaign_popup_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='donorrating',
            name='blood_request',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='donor_ratings', to='blood_requests_app.bloodrequest'),
        ),
        migrations.AlterField(
            model_name='donorrating',
            name='donor',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='received_ratings', to='accounts.user'),
        ),
        migrations.AlterField(
            model_name='donorrating',
            name='rater',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='given_ratings', to='accounts.user'),
        ),
    ]
