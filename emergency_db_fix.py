#!/usr/bin/env python
"""
Emergency database fix script - adds missing columns directly
This runs BEFORE Django setup to avoid ORM errors
"""
import os
import sys
import time

# Try importing psycopg2 (v2) or psycopg (v3)
try:
    import psycopg2
    from psycopg2 import sql, OperationalError
    HAS_PSYCOPG2 = True
    print("✅ Using psycopg2 (v2)")
except ImportError:
    try:
        import psycopg
        from psycopg import sql
        from psycopg.errors import OperationalError
        HAS_PSYCOPG2 = False
        print("✅ Using psycopg (v3)")
    except ImportError:
        print("❌ ERROR: Neither psycopg2 nor psycopg is installed!")
        print("Please run: pip install psycopg2-binary OR pip install 'psycopg[binary]'")
        sys.exit(1)

def get_database_config():
    """Get database configuration from environment variables"""
    return {
        'dbname': os.environ.get('SUPABASE_DB_NAME') or os.environ.get('PGDATABASE') or 'postgres',
        'user': os.environ.get('SUPABASE_USER') or os.environ.get('PGUSER') or 'postgres',
        'password': os.environ.get('SUPABASE_PASSWORD') or os.environ.get('PGPASSWORD'),
        'host': os.environ.get('SUPABASE_HOST') or os.environ.get('PGHOST') or 'localhost',
        'port': os.environ.get('SUPABASE_PORT') or os.environ.get('PGPORT') or '5432',
    }

def check_and_fix_columns():
    """Check for missing columns and add them if needed"""
    print("=" * 70)
    print("EMERGENCY DATABASE FIX - Adding Missing Columns")
    print("=" * 70)
    
    db_config = get_database_config()
    
    # Validate config
    if not db_config['password']:
        print("❌ ERROR: Database password not found in environment variables")
        print(f"   Available env vars: {list(os.environ.keys())}")
        return False
    
    print(f"\n📡 Connecting to database: {db_config['host']}/{db_config['dbname']}")
    
    try:
        # Connect to PostgreSQL (works with both psycopg2 and psycopg v3)
        if HAS_PSYCOPG2:
            conn = psycopg2.connect(**db_config)
            conn.autocommit = True
        else:
            conn = psycopg.connect(**db_config)
            conn.autocommit = True
        cursor = conn.cursor()
        
        print("✅ Connected successfully!\n")
        
        # Check and fix status_history column
        print("🔍 Checking for status_history column...")
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_schema = 'public'
            AND table_name = 'blood_requests_app_bloodrequest' 
            AND column_name = 'status_history'
        """)
        
        exists = cursor.fetchone()[0] > 0
        
        if exists:
            print("✅ status_history column already exists\n")
        else:
            print("⚠️  status_history column MISSING - Adding now...")
            try:
                # Try JSONB first (PostgreSQL native, better performance)
                cursor.execute("""
                    ALTER TABLE blood_requests_app_bloodrequest 
                    ADD COLUMN status_history JSONB DEFAULT '[]'::jsonb
                """)
                print("✅ status_history column added (JSONB type)\n")
            except Exception as e:
                print(f"⚠️  JSONB failed ({str(e)[:100]}), trying TEXT...")
                try:
                    # Fallback to TEXT
                    cursor.execute("""
                        ALTER TABLE blood_requests_app_bloodrequest 
                        ADD COLUMN status_history TEXT DEFAULT '[]'
                    """)
                    print("✅ status_history column added (TEXT type)\n")
                except Exception as e2:
                    print(f"❌ FAILED to add status_history: {e2}\n")
                    cursor.close()
                    conn.close()
                    return False
        
        # Also check for other critical columns that might be missing
        critical_columns = {
            'activated_at': 'TIMESTAMP NULL',
            'max_donors': 'INTEGER DEFAULT 5',
            'auto_expire_hours': 'INTEGER DEFAULT 6',
            'tracking_enabled': 'BOOLEAN DEFAULT TRUE',
            'exact_address': 'TEXT DEFAULT \'\'',
        }
        
        for col_name, col_type in critical_columns.items():
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_schema = 'public'
                AND table_name = 'blood_requests_app_bloodrequest' 
                AND column_name = '{col_name}'
            """)
            
            if cursor.fetchone()[0] == 0:
                print(f"⚠️  Adding missing column: {col_name}...")
                try:
                    cursor.execute(f"""
                        ALTER TABLE blood_requests_app_bloodrequest 
                        ADD COLUMN {col_name} {col_type}
                    """)
                    print(f"✅ {col_name} added\n")
                except Exception as e:
                    print(f"❌ Failed to add {col_name}: {e}\n")
            else:
                print(f"✅ {col_name} already exists")
        
        # Verify all columns exist
        print("\n" + "=" * 70)
        print("FINAL VERIFICATION")
        print("=" * 70)
        
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'public'
            AND table_name = 'blood_requests_app_bloodrequest' 
            AND column_name IN ('status_history', 'activated_at', 'max_donors', 
                               'auto_expire_hours', 'tracking_enabled', 'exact_address')
            ORDER BY column_name
        """)
        
        existing_cols = cursor.fetchall()
        print(f"\nFound {len(existing_cols)} tracked columns:")
        for col_name, data_type in existing_cols:
            print(f"   ✅ {col_name:25s} ({data_type})")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 70)
        print("✅ DATABASE FIX COMPLETED SUCCESSFULLY!")
        print("=" * 70 + "\n")
        return True
        
    except OperationalError as e:
        print(f"\n❌ CONNECTION ERROR: {e}")
        print("\nTroubleshooting:")
        print("  1. Check if SUPABASE_* environment variables are set correctly")
        print("  2. Verify database host is accessible")
        print("  3. Check firewall/network settings")
        print(f"\nCurrent config: host={db_config['host']}, db={db_config['dbname']}, user={db_config['user']}")
        return False
        
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = check_and_fix_columns()
    sys.exit(0 if success else 1)
