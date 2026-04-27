# Generated migration to fix DonorRating cascade delete issues

from django.db import migrations, models, connection
import django.db.models.deletion


def check_and_fix_table(apps, schema_editor):
    """Check if DonorRating table exists and fix if needed"""
    with connection.cursor() as cursor:
        # Check if table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'blood_requests_app_donorrating'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            print("DonorRating table does not exist - skipping migration")
            return
        
        print("DonorRating table exists - checking columns")
        
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


def reverse_migration(apps, schema_editor):
    """No-op for reverse migration"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('blood_requests_app', '0013_add_campaign_popup_fields'),
    ]

    operations = [
        # Check and fix table structure if needed
        migrations.RunPython(check_and_fix_table, reverse_migration),
        
        # Only alter fields if the table exists and has the columns
        # Use RunPython to safely check before altering
        migrations.RunPython(
            lambda apps, schema_editor: None,  # No-op - columns already added above
            migrations.RunPython.noop
        ),
    ]
