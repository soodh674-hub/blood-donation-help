"""
Emergency fix for migration state mismatch
This script marks migrations as applied without actually running them
Use this when columns already exist in the database but Django doesn't know about it
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blood_donation.settings')
django.setup()

from django.db import connection
from django.db.migrations.recorder import MigrationRecorder

def check_column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = %s AND column_name = %s;
        """, [table_name, column_name])
        return cursor.fetchone() is not None

def is_migration_applied(app_label, migration_name):
    """Check if migration is recorded as applied"""
    recorder = MigrationRecorder(connection)
    applied = recorder.applied_migrations()
    return (app_label, migration_name) in applied

def mark_migration_applied(app_label, migration_name):
    """Mark a migration as applied in Django's migration history"""
    recorder = MigrationRecorder(connection)
    recorder.record_applied(app_label, migration_name)
    print(f"✓ Marked {app_label}.{migration_name} as applied")

def main():
    print("=" * 60)
    print("DATABASE MIGRATION STATE FIX")
    print("=" * 60)
    
    # Check migration 0016
    app_label = 'accounts'
    migration_name = '0016_add_hospital_complete_fields'
    
    print(f"\nChecking if {app_label}.{migration_name} is applied...")
    
    if is_migration_applied(app_label, migration_name):
        print("✓ Migration is already recorded as applied")
        print("No action needed!")
        return
    
    print("✗ Migration is NOT recorded as applied")
    print("\nChecking if columns already exist in database...")
    
    # Check if the columns from migration 0016 exist
    columns_to_check = [
        'has_blood_bank',
        'blood_groups_available',
        'verified_by_id',
        'verified_at',
        'verification_documents',
        'total_donations_processed',
        'active_requests',
        'trust_score',
    ]
    
    existing_columns = []
    missing_columns = []
    
    for col in columns_to_check:
        exists = check_column_exists('accounts_hospital', col)
        if exists:
            existing_columns.append(col)
            print(f"  ✓ Column '{col}' exists")
        else:
            missing_columns.append(col)
            print(f"  ✗ Column '{col}' missing")
    
    print(f"\nResults: {len(existing_columns)} exist, {len(missing_columns)} missing")
    
    if missing_columns:
        print("\n❌ ERROR: Some columns are missing!")
        print("You need to run the actual migration, not just mark it as applied.")
        print(f"Missing columns: {', '.join(missing_columns)}")
        print("\nRun: python manage.py migrate accounts 0016")
        return
    
    if existing_columns:
        print("\n✓ All columns already exist in database!")
        print("This means the migration was run manually or partially applied.")
        print("\nSolution: Mark migration as applied in Django's history")
        
        confirm = input("\nMark migration as applied? (yes/no): ")
        if confirm.lower() == 'yes':
            mark_migration_applied(app_label, migration_name)
            print("\n✅ SUCCESS! Migration marked as applied.")
            print("The app should now work correctly.")
        else:
            print("\nCancelled. No changes made.")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    main()
