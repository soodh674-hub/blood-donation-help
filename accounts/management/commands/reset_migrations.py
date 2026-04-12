from django.core.management.base import BaseCommand
from django.db import connection
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Reset database migrations (USE WITH CAUTION - for development only)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Actually reset migrations (DANGEROUS)',
        )

    def handle(self, *args, **options):
        if not options['reset']:
            self.stdout.write(self.style.WARNING("DRY RUN - This would reset all migrations. Use --reset to actually do it."))
            return

        self.stdout.write(self.style.ERROR("WARNING: This will delete all data and reset migrations!"))
        confirm = input("Type 'YES' to confirm: ")
        if confirm != 'YES':
            self.stdout.write("Aborted.")
            return

        try:
            with connection.cursor() as cursor:
                # Drop all tables (this is very dangerous!)
                cursor.execute("""
                    DROP SCHEMA public CASCADE;
                    CREATE SCHEMA public;
                """)
            
            self.stdout.write(self.style.SUCCESS("Database schema reset!"))
            self.stdout.write("Now run: python manage.py migrate")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error resetting database: {e}"))
            logger.error(f"Database reset error: {e}", exc_info=True)