# Generated migration to add missing Hospital model fields
# These fields were added to the model but migration was not created
# Updated: Added conditional checks to handle existing columns

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def add_field_if_not_exists(apps, schema_editor):
    """Add fields only if they don't already exist"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Get existing columns
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'accounts_hospital';
        """)
        existing_columns = {row[0] for row in cursor.fetchall()}
    
    db_table = 'accounts_hospital'
    
    # Define fields to add with raw SQL
    fields_sql = [
        ('has_blood_bank', 'ALTER TABLE {} ADD COLUMN has_blood_bank boolean DEFAULT true'),
        ('blood_groups_available', 'ALTER TABLE {} ADD COLUMN blood_groups_available jsonb DEFAULT \'[]\'::jsonb'),
        ('verified_by_id', 'ALTER TABLE {} ADD COLUMN verified_by_id integer NULL'),
        ('verified_at', 'ALTER TABLE {} ADD COLUMN verified_at timestamp with time zone NULL'),
        ('verification_documents', 'ALTER TABLE {} ADD COLUMN verification_documents varchar(100) NULL'),
        ('total_donations_processed', 'ALTER TABLE {} ADD COLUMN total_donations_processed integer DEFAULT 0'),
        ('active_requests', 'ALTER TABLE {} ADD COLUMN active_requests integer DEFAULT 0'),
        ('trust_score', 'ALTER TABLE {} ADD COLUMN trust_score integer DEFAULT 50'),
    ]
    
    for field_name, sql_template in fields_sql:
        if field_name not in existing_columns:
            sql = sql_template.format(db_table)
            try:
                with connection.cursor() as cursor:
                    cursor.execute(sql)
                print(f"  ✓ Added column: {field_name}")
            except Exception as e:
                print(f"  ⚠ Column {field_name} might already exist: {str(e)}")
        else:
            print(f"  ⊘ Skipping {field_name} - already exists")


def add_indexes_if_not_exists(apps, schema_editor):
    """Add indexes only if they don't already exist"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Check if indexes exist
        cursor.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'accounts_hospital';
        """)
        existing_indexes = {row[0] for row in cursor.fetchall()}
    
    # Add indexes using raw SQL
    indexes_sql = [
        ('accounts_ho_city_abc123_idx', 
         'CREATE INDEX accounts_ho_city_abc123_idx ON accounts_hospital (city, verification_status)'),
        ('accounts_ho_trust_s_def456_idx', 
         'CREATE INDEX accounts_ho_trust_s_def456_idx ON accounts_hospital (trust_score)'),
    ]
    
    for index_name, sql in indexes_sql:
        if index_name not in existing_indexes:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(sql)
                print(f"  ✓ Created index: {index_name}")
            except Exception as e:
                print(f"  ⚠ Index {index_name} might already exist: {str(e)}")
        else:
            print(f"  ⊘ Skipping index {index_name} - already exists")


def remove_is_active_if_exists(apps, schema_editor):
    """Remove is_active field only if it exists"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'accounts_hospital' AND column_name = 'is_active';
        """)
        if cursor.fetchone():
            try:
                with connection.cursor() as cursor:
                    cursor.execute("ALTER TABLE accounts_hospital DROP COLUMN is_active")
                print("  ✓ Removed is_active column")
            except Exception as e:
                print(f"  ⚠ Could not remove is_active: {str(e)}")
        else:
            print("  ⊘ is_active column doesn't exist, skipping")


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0015_fix_cascade_delete'),
    ]

    operations = [
        # Use RunPython to conditionally add fields
        migrations.RunPython(add_field_if_not_exists, migrations.RunPython.noop),
        
        # Remove old is_active field if it exists
        migrations.RunPython(remove_is_active_if_exists, migrations.RunPython.noop),
        
        # Add indexes using raw SQL (avoids FieldDoesNotExist errors)
        migrations.RunPython(add_indexes_if_not_exists, migrations.RunPython.noop),
    ]
