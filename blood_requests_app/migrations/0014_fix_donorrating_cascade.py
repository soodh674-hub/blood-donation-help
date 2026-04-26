# Generated migration to fix DonorRating cascade delete issues

from django.db import migrations, models, connection
import django.db.models.deletion


def add_missing_columns(apps, schema_editor):
    """Add missing columns if they don't exist"""
    with connection.cursor() as cursor:
        # Check if table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'blood_requests_app_donorrating'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            # Check if blood_request_id column exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'blood_requests_app_donorrating'
                    AND column_name = 'blood_request_id'
                );
            """)
            blood_request_exists = cursor.fetchone()[0]
            
            if not blood_request_exists:
                cursor.execute("""
                    ALTER TABLE blood_requests_app_donorrating
                    ADD COLUMN blood_request_id INTEGER NULL;
                """)
                print("Added blood_request_id column")
            
            # Check if donor_id column exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'blood_requests_app_donorrating'
                    AND column_name = 'donor_id'
                );
            """)
            donor_exists = cursor.fetchone()[0]
            
            if not donor_exists:
                cursor.execute("""
                    ALTER TABLE blood_requests_app_donorrating
                    ADD COLUMN donor_id INTEGER NULL;
                """)
                print("Added donor_id column")
            
            # Check if rater_id column exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'blood_requests_app_donorrating'
                    AND column_name = 'rater_id'
                );
            """)
            rater_exists = cursor.fetchone()[0]
            
            if not rater_exists:
                cursor.execute("""
                    ALTER TABLE blood_requests_app_donorrating
                    ADD COLUMN rater_id INTEGER NULL;
                """)
                print("Added rater_id column")


class Migration(migrations.Migration):

    dependencies = [
        ('blood_requests_app', '0013_add_campaign_popup_fields'),
    ]

    operations = [
        # First add missing columns if they don't exist
        migrations.RunPython(add_missing_columns, migrations.RunPython.noop),
        
        # Then try to alter fields (this will be idempotent)
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
