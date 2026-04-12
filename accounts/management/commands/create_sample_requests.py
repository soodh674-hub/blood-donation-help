"""
Management command to create sample blood requests for testing
Usage: python manage.py create_sample_requests
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from blood_requests_app.models import BloodRequest


class Command(BaseCommand):
    help = 'Create sample blood requests for testing the live requests feature'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting to create sample blood requests...'))
        
        # Get or create a test user (superuser if exists)
        try:
            requester = User.objects.filter(is_superuser=True).first()
            if not requester:
                requester = User.objects.filter(user_type='donor').first()
            
            if not requester:
                self.stdout.write(self.style.ERROR('No users found in database. Please create a user first.'))
                return
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error finding user: {str(e)}'))
            return
        
        # Sample blood requests data
        sample_requests = [
            {
                'patient_name': 'Rajesh Kumar',
                'patient_age': 45,
                'patient_blood_group': 'A+',
                'required_units': 2,
                'reason': 'Emergency surgery - cardiac bypass',
                'priority': 'emergency',
                'hospital_name': 'AIIMS Delhi',
                'city': 'New Delhi',
                'state': 'Delhi',
                'pincode': '110029',
                'contact_person': 'Dr. Sharma',
                'contact_phone': '9876543210',
                'contact_email': 'aiims.emergency@example.com',
                'requester_type': 'hospital',
            },
            {
                'patient_name': 'Priya Singh',
                'patient_age': 28,
                'patient_blood_group': 'O-',
                'required_units': 1,
                'reason': 'Postpartum hemorrhage',
                'priority': 'emergency',
                'hospital_name': 'Safdarjung Hospital',
                'city': 'New Delhi',
                'state': 'Delhi',
                'pincode': '110029',
                'contact_person': 'Dr. Verma',
                'contact_phone': '9123456789',
                'contact_email': 'safdarjung.emergency@example.com',
                'requester_type': 'hospital',
            },
            {
                'patient_name': 'Mohammad Arif',
                'patient_age': 35,
                'patient_blood_group': 'B+',
                'required_units': 3,
                'reason': 'Trauma - multiple injuries from accident',
                'priority': 'urgent',
                'hospital_name': 'LNJP Hospital',
                'city': 'New Delhi',
                'state': 'Delhi',
                'pincode': '110002',
                'contact_person': 'Dr. Gupta',
                'contact_phone': '9988776655',
                'contact_email': 'lnjp.emergency@example.com',
                'requester_type': 'hospital',
            },
            {
                'patient_name': 'Sunita Devi',
                'patient_age': 52,
                'patient_blood_group': 'AB+',
                'required_units': 2,
                'reason': 'Liver transplant surgery',
                'priority': 'urgent',
                'hospital_name': 'ILBS Delhi',
                'city': 'New Delhi',
                'state': 'Delhi',
                'pincode': '110006',
                'contact_person': 'Dr. Kumar',
                'contact_phone': '9876512340',
                'contact_email': 'ilbs.transplant@example.com',
                'requester_type': 'hospital',
            },
            {
                'patient_name': 'Vikram Malhotra',
                'patient_age': 60,
                'patient_blood_group': 'A-',
                'required_units': 4,
                'reason': 'Cancer treatment - chemotherapy support',
                'priority': 'normal',
                'hospital_name': 'Rajiv Gandhi Cancer Institute',
                'city': 'New Delhi',
                'state': 'Delhi',
                'pincode': '110085',
                'contact_person': 'Dr. Mehta',
                'contact_phone': '9123498765',
                'contact_email': 'rgci.oncology@example.com',
                'requester_type': 'hospital',
            },
            {
                'patient_name': 'Anita Sharma',
                'patient_age': 30,
                'patient_blood_group': 'O+',
                'required_units': 2,
                'reason': 'Dengue fever - low platelet count',
                'priority': 'normal',
                'hospital_name': 'Max Super Speciality Hospital',
                'city': 'Saket',
                'state': 'Delhi',
                'pincode': '110017',
                'contact_person': 'Dr. Agarwal',
                'contact_phone': '9876123450',
                'contact_email': 'max.saket@example.com',
                'requester_type': 'hospital',
            },
        ]
        
        created_count = 0
        now = timezone.now()
        
        for i, data in enumerate(sample_requests):
            try:
                # Create blood request
                blood_request = BloodRequest.objects.create(
                    patient_name=data['patient_name'],
                    patient_age=data['patient_age'],
                    patient_blood_group=data['patient_blood_group'],
                    required_units=data['required_units'],
                    reason=data['reason'],
                    priority=data['priority'],
                    hospital_name=data['hospital_name'],
                    city=data['city'],
                    state=data['state'],
                    pincode=data['pincode'],
                    contact_person=data['contact_person'],
                    contact_phone=data['contact_phone'],
                    contact_email=data['contact_email'],
                    requester=requester,
                    requester_type=data['requester_type'],
                    status='active',
                    required_by=now + timedelta(hours=(i + 1) * 2),  # Staggered timing
                    expires_at=now + timedelta(days=7),  # Valid for 7 days
                )
                
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Created {data["priority"].upper()} request: '
                        f'{data["patient_blood_group"]} blood for {data["hospital_name"]}'
                    )
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ Failed to create request for {data["patient_name"]}: {str(e)}'
                    )
                )
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS(f'✅ Successfully created {created_count} sample blood requests!'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(self.style.SUCCESS('\nRefresh your homepage to see the live blood requests.'))
        self.stdout.write(self.style.SUCCESS('The requests will appear in the "Live Blood Requests" section.\n'))
