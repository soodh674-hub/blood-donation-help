# Generated migration for FavoriteDonor model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_add_profile_photo'),
    ]

    operations = [
        migrations.CreateModel(
            name='FavoriteDonor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('notes', models.TextField(blank=True, help_text='Personal notes about this donor')),
                ('favorite_donor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favorited_by', to='accounts.user')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favorite_donors', to='accounts.user')),
            ],
            options={
                'verbose_name': 'Favorite Donor',
                'verbose_name_plural': 'Favorite Donors',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='favoritedonor',
            unique_together={('user', 'favorite_donor')},
        ),
    ]
