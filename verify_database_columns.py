#!/usr/bin/env python
"""
Database column verification script for BloodLife application
This script verifies that all critical columns exist in the database
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blood_donation.settings')
django.setup()

from django.db import connection
from django.core.management.base import BaseCommand
from django.apps import apps

def verify_blood_request_columns():
    """Verify critical columns in blood_requests_app_bloodrequest table"""
    critical_columns = [
        # Core fields
        'id', 'requester_id', 'patient_name', 'patient_age', 'patient_blood_group',
        'required_units', 'fulfilled_units', 'priority', 'status', 'requester_type',
        
        # Medical details
        'reason', 'required_by', 'medical_certificate', 'is_critical',
        
        # Location fields
        'hospital_name', 'city', 'state', 'country', 'pincode', 
        'latitude', 'longitude', 'exact_address',
        
        # Contact information
        'contact_person', 'contact_phone', 'contact_email',
        
        # Approval workflow
        'approved_by_id', 'approved_at', 'approval_notes',
        
        # Real-time tracking fields
        'max_donors', 'auto_expire_hours', 'tracking_enabled',
        
        # Timestamps
        'created_at', 'updated_at', 'expires_at', 'activated_at',
    ]
    
    print("🔍 Verifying blood_requests_app_bloodrequest table columns...")
    
    with connection.cursor() as cursor:
        # Get existing columns
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'blood_requests_app_bloodrequest'
            ORDER BY ordinal_position
        """)
        
        existing_columns = cursor.fetchall()
        existing_column_names = [col[0] for col in existing_columns]
        
        print(f"📊 Found {len(existing_columns)} columns:")
        for col in existing_columns:
            print(f"  ✓ {col[0]} ({col[1]})")
        
        # Check for missing columns
        missing_columns = set(critical_columns) - set(existing_column_names)
        extra_columns = set(existing_column_names) - set(critical_columns)
        
        if missing_columns:
            print(f"\n❌ MISSING COLUMNS ({len(missing_columns)}):")
            for col in missing_columns:
                print(f"  🔴 {col}")
            
            print("\n🔧 SQL to add missing columns:")
            for col in missing_columns:
                if col in ['max_donors', 'auto_expire_hours']:
                    sql = f"ALTER TABLE blood_requests_app_bloodrequest ADD COLUMN {col} INTEGER DEFAULT 5;"
                elif col == 'tracking_enabled':
                    sql = f"ALTER TABLE blood_requests_app_bloodrequest ADD COLUMN {col} BOOLEAN DEFAULT TRUE;"
                elif col in ['latitude', 'longitude']:
                    sql = f"ALTER TABLE blood_requests_app_bloodrequest ADD COLUMN {col} DECIMAL(9,6) NULL;"
                elif col in ['expires_at', 'activated_at', 'approved_at']:
                    sql = f"ALTER TABLE blood_requests_app_bloodrequest ADD COLUMN {col} TIMESTAMP NULL;"
                elif col in ['exact_address']:
                    sql = f"ALTER TABLE blood_requests_app_bloodrequest ADD COLUMN {col} TEXT NULL;"
                elif col.endswith('_id'):
                    sql = f"ALTER TABLE blood_requests_app_bloodrequest ADD COLUMN {col} INTEGER NULL;"
                else:
                    sql = f"ALTER TABLE blood_requests_app_bloodrequest ADD COLUMN {col} VARCHAR(200) NULL;"
                print(f"  {sql}")
        else:
            print("\n✅ All critical columns are present!")
        
        if extra_columns:
            print(f"\n📝 EXTRA COLUMNS ({len(extra_columns)}):")
            for col in extra_columns:
                print(f"  ➕ {col}")
    
    return len(missing_columns) == 0

def verify_request_response_columns():
    """Verify critical columns in blood_requests_app_requestresponse table"""
    critical_columns = [
        'id', 'request_id', 'donor_id', 'status', 'responded_at',
        'en_route_at', 'arrived_at', 'completed_at',
        'donor_latitude', 'donor_longitude', 'last_location_update',
        'distance_km', 'estimated_arrival_minutes', 'is_selected', 'selected_at', 'notes'
    ]
    
    print("\n🔍 Verifying blood_requests_app_requestresponse table columns...")
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'blood_requests_app_requestresponse'
                ORDER BY ordinal_position
            """)
            
            existing_columns = cursor.fetchall()
            existing_column_names = [col[0] for col in existing_columns]
            
            print(f"📊 Found {len(existing_columns)} columns:")
            for col in existing_columns:
                print(f"  ✓ {col[0]} ({col[1]})")
            
            # Check for missing columns
            missing_columns = set(critical_columns) - set(existing_column_names)
            
            if missing_columns:
                print(f"\n❌ MISSING COLUMNS ({len(missing_columns)}):")
                for col in missing_columns:
                    print(f"  🔴 {col}")
            else:
                print("\n✅ All request response columns are present!")
            
            return len(missing_columns) == 0
    
    except Exception as e:
        print(f"⚠️  Could not verify requestresponse table: {e}")
        return False

def verify_indexes():
    """Verify important indexes exist"""
    print("\n🔍 Verifying database indexes...")
    
    expected_indexes = [
        'blood_requests_bloodrequest_status_priority_idx',
        'blood_requests_bloodrequest_city_patient_blood_group_idx',
        'blood_requests_bloodrequest_latitude_longitude_idx',
    ]
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT indexname, tablename
                FROM pg_indexes
                WHERE tablename IN ('blood_requests_app_bloodrequest', 'blood_requests_app_requestresponse')
                ORDER BY indexname
            """)
            
            existing_indexes = cursor.fetchall()
            existing_index_names = [idx[0] for idx in existing_indexes]
            
            print(f"📊 Found {len(existing_indexes)} indexes:")
            for idx in existing_indexes:
                print(f"  ✓ {idx[0]} on {idx[1]}")
            
            # Check for missing indexes
            missing_indexes = set(expected_indexes) - set(existing_index_names)
            
            if missing_indexes:
                print(f"\n⚠️  MISSING INDEXES ({len(missing_indexes)}):")
                for idx in missing_indexes:
                    print(f"  🔴 {idx}")
            else:
                print("\n✅ All critical indexes are present!")
            
            return len(missing_indexes) == 0
    
    except Exception as e:
        print(f"⚠️  Could not verify indexes: {e}")
        return False

def main():
    """Main verification function"""
    print("🚀 BloodLife Database Verification Script")
    print("=" * 50)
    
    try:
        # Verify BloodRequest table
        blood_request_ok = verify_blood_request_columns()
        
        # Verify RequestResponse table
        response_ok = verify_request_response_columns()
        
        # Verify indexes
        indexes_ok = verify_indexes()
        
        print("\n" + "=" * 50)
        print("📋 VERIFICATION SUMMARY:")
        print(f"  BloodRequest Table: {'✅ OK' if blood_request_ok else '❌ ISSUES'}")
        print(f"  RequestResponse Table: {'✅ OK' if response_ok else '❌ ISSUES'}")
        print(f"  Database Indexes: {'✅ OK' if indexes_ok else '❌ ISSUES'}")
        
        if blood_request_ok and response_ok and indexes_ok:
            print("\n🎉 All verifications passed! Database is ready.")
            return 0
        else:
            print("\n⚠️  Some verifications failed. Please review the issues above.")
            return 1
            
    except Exception as e:
        print(f"\n💥 Verification failed with error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
