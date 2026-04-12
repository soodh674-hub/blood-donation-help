from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from notifications.models import Notification
from notifications.services import NotificationService

User = get_user_model()

class Command(BaseCommand):
    help = 'Create test notifications for demonstration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-email',
            type=str,
            help='Email of user to create notifications for (optional)',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Create notifications for all users',
        )

    def handle(self, *args, **options):
        user_email = options['user_email']
        create_for_all = options['all']
        
        if create_for_all:
            users = User.objects.all()
            self.stdout.write(f"Creating notifications for {users.count()} users...")
            for user in users:
                self.create_test_notifications(user)
        elif user_email:
            try:
                user = User.objects.get(email=user_email)
                self.create_test_notifications(user)
            except User.DoesNotExist:
                raise CommandError(f"No user found with email {user_email}")
        else:
            # Create for first active user
            user = User.objects.filter(is_active=True).first()
            if not user:
                raise CommandError("No active users found. Create a user first!")
            self.create_test_notifications(user)
        
        self.stdout.write(self.style.SUCCESS('Successfully created test notifications!'))

    def create_test_notifications(self, user):
        """Create sample notifications for a user"""
        self.stdout.write(f"Creating notifications for {user.email}...")
        
        # Clear existing test notifications
        Notification.objects.filter(user=user).delete()
        
        # 1. Welcome notification
        NotificationService.create_notification(
            user=user,
            notification_type='general',
            title='🎉 Welcome to BloodLife!',
            message=f"Welcome {user.first_name or 'friend'}! You've successfully joined our life-saving community. Complete your profile to start making a difference!",
            priority='medium',
            category='system',
            expires_hours=72
        )
        
        # 2. Profile completion reminder
        if not user.blood_group or not user.phone_number:
            NotificationService.create_notification(
                user=user,
                notification_type='status_update',
                title='📋 Complete Your Profile',
                message='Please update your blood group and phone number to help patients find compatible donors quickly.',
                priority='high',
                category='system',
                expires_hours=48
            )
        
        # 3. Sample blood request notification
        NotificationService.create_notification(
            user=user,
            notification_type='blood_request',
            title='🩸 Urgent Blood Request Nearby',
            message=f"A patient near you needs {user.blood_group or 'O+'} blood urgently. Contact the hospital immediately if you can help!",
            priority='urgent',
            category='medical',
            expires_hours=24
        )
        
        # 4. Eligibility reminder (if last donation was long ago)
        if user.last_donation_date:
            days_since = (timezone.now().date() - user.last_donation_date).days
            if days_since > 60:
                NotificationService.create_notification(
                    user=user,
                    notification_type='eligibility',
                    title='✅ You\'re Eligible to Donate Again!',
                    message=f"It's been {days_since} days since your last donation. You're now eligible to donate blood again and save lives!",
                    priority='medium',
                    category='health',
                    expires_hours=72
                )
        
        # 5. Donation reminder
        NotificationService.create_notification(
            user=user,
            notification_type='donation_reminder',
            title='💪 Be a Hero - Donate Today!',
            message='Regular blood donations can save up to 3 lives per donation. Schedule your appointment today!',
            priority='low',
            category='reminder',
            expires_hours=168
        )
        
        self.stdout.write(f"  ✓ Created 5 sample notifications for {user.email}")
