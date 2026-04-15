from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from blood_requests_app.models import BloodRequest
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Create sample blood requests with future expiration dates for testing'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample blood requests...')
        
        User = get_user_model()
        
        # Get or create a test user
        test_user, created = User.objects.get_or_create(
            username='test_requester',
            defaults={
                'email': 'test@bloodlife.com',
                'first_name': 'Test',
                'last_name': 'User',
                'blood_group': 'O+',
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'is_donor': True,
            }
        )
        
        if created:
            test_user.set_password('testpass123')
            test_user.save()
            self.stdout.write(self.style.SUCCESS(f'✓ Created test user: {test_user.username}'))
        
        # Sample requests data
        sample_requests = [
            {
                'patient_name': 'Rahul Sharma',
                'patient_age': 45,
                'patient_blood_group': 'A+',
                'required_units': 2,
                'priority': 'urgent',
                'hospital_name': 'Apollo Hospital, Mumbai',
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'country': 'India',
                'pincode': '400001',
                'latitude': 19.0760,
                'longitude': 72.8777,
                'contact_person': 'Dr. Patel',
                'contact_phone': '+919876543210',
                'contact_email': 'test@bloodlife.com',
                'reason': 'Emergency surgery requiring blood transfusion',
            },
            {
                'patient_name': 'Priya Singh',
                'patient_age': 32,
                'patient_blood_group': 'B+',
                'required_units': 3,
                'priority': 'emergency',
                'hospital_name': 'Fortis Hospital, Delhi',
                'city': 'Delhi',
                'state': 'Delhi',
                'country': 'India',
                'pincode': '110001',
                'latitude': 28.7041,
                'longitude': 77.1025,
                'contact_person': 'Dr. Kumar',
                'contact_phone': '+919876543211',
                'contact_email': 'test@bloodlife.com',
                'reason': 'Accident victim needs immediate blood',
            },
            {
                'patient_name': 'Amit Patel',
                'patient_age': 58,
                'patient_blood_group': 'O-',
                'required_units': 1,
                'priority': 'normal',
                'hospital_name': 'AIIMS, New Delhi',
                'city': 'New Delhi',
                'state': 'Delhi',
                'country': 'India',
                'pincode': '110029',
                'latitude': 28.5672,
                'longitude': 77.2100,
                'contact_person': 'Nurse Sharma',
                'contact_phone': '+919876543212',
                'contact_email': 'test@bloodlife.com',
                'reason': 'Scheduled surgery next week',
            },
            {
                'patient_name': 'Sneha Reddy',
                'patient_age': 28,
                'patient_blood_group': 'AB+',
                'required_units': 2,
                'priority': 'urgent',
                'hospital_name': 'Narayana Health, Bangalore',
                'city': 'Bangalore',
                'state': 'Karnataka',
                'country': 'India',
                'pincode': '560001',
                'latitude': 12.9716,
                'longitude': 77.5946,
                'contact_person': 'Dr. Reddy',
                'contact_phone': '+919876543213',
                'contact_email': 'test@bloodlife.com',
                'reason': 'Complications during delivery',
            },
            {
                'patient_name': 'Vikram Mehta',
                'patient_age': 65,
                'patient_blood_group': 'A-',
                'required_units': 4,
                'priority': 'emergency',
                'hospital_name': 'CMC Vellore',
                'city': 'Vellore',
                'state': 'Tamil Nadu',
                'country': 'India',
                'pincode': '632004',
                'latitude': 12.9165,
                'longitude': 79.1325,
                'contact_person': 'Dr. Thomas',
                'contact_phone': '+919876543214',
                'contact_email': 'test@bloodlife.com',
                'reason': 'Critical heart surgery',
            },
        ]
        
        created_count = 0
        for req_data in sample_requests:
            # Set timestamps
            req_data['requester'] = test_user
            req_data['created_at'] = timezone.now()
            req_data['required_by'] = timezone.now() + timedelta(days=2)
            req_data['expires_at'] = timezone.now() + timedelta(days=7)
            req_data['status'] = 'active'
            
            # Create request
            request = BloodRequest.objects.create(**req_data)
            created_count += 1
            
            self.stdout.write(
                f'  ✓ Created Request #{request.id}: '
                f'{request.patient_blood_group} - {request.hospital_name} '
                f'({request.priority.upper()})'
            )
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Successfully created {created_count} sample blood requests!'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'📊 Total active requests: {BloodRequest.objects.filter(status="active").count()}'
        ))
        self.stdout.write(self.style.WARNING(
            '\n💡 Login credentials: test_requester / testpass123'
        ))
