#!/usr/bin/env python
"""
Generate migrations for model code changes
This creates empty migrations to acknowledge code-only changes
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blood_donation.settings')
django.setup()

from django.core.management import call_command

def main():
    print("=" * 60)
    print("GENERATING MIGRATIONS FOR CODE CHANGES")
    print("=" * 60)
    
    apps_to_check = ['accounts', 'blood_requests_app', 'donors', 'notifications']
    
    for app in apps_to_check:
        print(f"\nChecking {app}...")
        try:
            # First, check if there are actual changes
            call_command('makemigrations', app, '--dry-run', verbosity=2)
        except Exception as e:
            print(f"Note: {app} - {str(e)}")
    
    print("\n" + "=" * 60)
    print("Now creating migrations if needed...")
    print("=" * 60 + "\n")
    
    # Create migrations for all apps
    try:
        call_command('makemigrations', verbosity=2)
        print("\n✓ Migrations created successfully!")
    except Exception as e:
        print(f"\n✗ Error creating migrations: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Migration generation complete!")
    print("=" * 60)

if __name__ == '__main__':
    main()
