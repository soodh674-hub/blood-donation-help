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
    
    # Fields to add with their definitions
    fields_to_add = {
        'has_blood_bank': models.BooleanField(default=True),
        'blood_groups_available': models.JSONField(default=list, help_text='List of available blood groups'),
        'verified_by': models.ForeignKey(
            settings.AUTH_USER_MODEL,
            blank=True,
            null=True,
            on_delete=django.db.models.deletion.SET_NULL,
            related_name='verified_hospitals',
        ),
        'verified_at': models.DateTimeField(blank=True, null=True),
        'verification_documents': models.FileField(blank=True, null=True, upload_to='hospital_documents/'),
        'total_donations_processed': models.IntegerField(default=0),
        'active_requests': models.IntegerField(default=0),
        'trust_score': models.IntegerField(default=50, help_text='Trust score from 0-100'),
    }
    
    Hospital = apps.get_model('accounts', 'Hospital')
    
    for field_name, field in fields_to_add.items():
        if field_name not in existing_columns:
            # Add the field to the model
            from django.db.migrations.state import ModelState
            state = ModelState.from_model(Hospital)
            state.fields.append((field_name, field))
            
            # Execute the ADD COLUMN SQL
            db_table = Hospital._meta.db_table
            column_name = field_name
            if field_name.endswith('_id'):
                column_name = field_name  # Foreign key
            
            # Get the column type
            from django.db.backends.base.schema import BaseDatabaseSchemaEditor
            field.set_attributes_from_name(field_name)
            field_type = schema_editor.column_sql(Hospital, field)
            
            nullable = 'NULL' if field.null else 'NOT NULL'
            default = ''
            if field.has_default():
                default_value = field.get_default()
                if isinstance(default_value, bool):
                    default = f"DEFAULT {'TRUE' if default_value else 'FALSE'}"
                elif isinstance(default_value, (int, float)):
                    default = f"DEFAULT {default_value}"
                elif isinstance(default_value, (list, dict)):
                    default = f"DEFAULT '{str(default_value)}'"
            
            sql = f"ALTER TABLE {db_table} ADD COLUMN {column_name} {field_type} {nullable} {default}"
            
            try:
                with connection.cursor() as cursor:
                    cursor.execute(sql)
                print(f"  ✓ Added column: {field_name}")
            except Exception as e:
                print(f"  ⚠ Column {field_name} might already exist: {str(e)}")
        else:
            print(f"  ⊘ Skipping {field_name} - already exists")


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
        
        # Add indexes for better query performance
        migrations.AddIndex(
            model_name='hospital',
            index=models.Index(fields=['city', 'verification_status'], name='accounts_ho_city_abc123_idx'),
        ),
        migrations.AddIndex(
            model_name='hospital',
            index=models.Index(fields=['trust_score'], name='accounts_ho_trust_s_def456_idx'),
        ),
    ]
