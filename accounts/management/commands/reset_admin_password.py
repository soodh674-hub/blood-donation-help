"""
Management command to reset admin password
Usage: python manage.py reset_admin_password --email admin@example.com --password newpassword123
"""
from django.core.management.base import BaseCommand, CommandError
from accounts.models import User


class Command(BaseCommand):
    help = 'Reset admin user password'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            required=True,
            help='Email address of the admin user'
        )
        parser.add_argument(
            '--password',
            type=str,
            required=True,
            help='New password for the admin user'
        )

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        
        try:
            # Find the admin user
            admin_user = User.objects.get(email=email, is_staff=True)
            
            # Set new password
            admin_user.set_password(password)
            admin_user.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully reset password for admin user: {email}')
            )
        except User.DoesNotExist:
            raise CommandError(f'No admin user found with email: {email}')
        except Exception as e:
            raise CommandError(f'Error resetting password: {str(e)}')
