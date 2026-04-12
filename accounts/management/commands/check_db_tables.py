from django.core.management.base import BaseCommand
from django.db import connection
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Check database tables and their status'

    def handle(self, *args, **options):
        self.stdout.write("=== DATABASE TABLE STATUS ===")
        
        try:
            with connection.cursor() as cursor:
                # Check if accounts_user table exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'accounts_user'
                    );
                """)
                accounts_user_exists = cursor.fetchone()[0]
                
                # Check if auth_user table exists (Django's default user table)
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'auth_user'
                    );
                """)
                auth_user_exists = cursor.fetchone()[0]
                
                # List all tables
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name;
                """)
                all_tables = [row[0] for row in cursor.fetchall()]
                
            self.stdout.write(f"accounts_user table exists: {'YES' if accounts_user_exists else 'NO'}")
            self.stdout.write(f"auth_user table exists: {'YES' if auth_user_exists else 'NO'}")
            self.stdout.write(f"\nAll tables in database ({len(all_tables)}):")
            for table in all_tables:
                self.stdout.write(f"  - {table}")
                
            # Check migration status
            self.stdout.write(f"\n=== MIGRATION STATUS ===")
            from django.db.migrations.executor import MigrationExecutor
            from django.db import connections
            
            connection = connections['default']
            executor = MigrationExecutor(connection)
            targets = executor.loader.graph.leaf_nodes()
            plan = executor.migration_plan(targets)
            
            if plan:
                self.stdout.write(f"Pending migrations: {len(plan)}")
                for migration, backwards in plan:
                    self.stdout.write(f"  - {migration.app_label}.{migration.name}")
            else:
                self.stdout.write("All migrations applied!")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error checking database: {e}"))
            logger.error(f"Database check error: {e}", exc_info=True)
            
        self.stdout.write("=== END DATABASE CHECK ===")