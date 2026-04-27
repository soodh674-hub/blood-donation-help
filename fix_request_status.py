"""
Quick fix script to update blood requests with incorrect status
Changes status from 'pending_verification' to 'pending'
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blood_donation.settings')
django.setup()

from blood_requests_app.models import BloodRequest

def fix_request_status():
    """Fix requests with incorrect status"""
    
    # Find all requests with the wrong status
    wrong_status_requests = BloodRequest.objects.filter(status='pending_verification')
    
    count = wrong_status_requests.count()
    
    if count == 0:
        print("✅ No requests found with 'pending_verification' status.")
        print("All requests have correct status!")
        return
    
    print(f"🔍 Found {count} request(s) with incorrect status 'pending_verification'")
    print("\nRequests to update:")
    for req in wrong_status_requests:
        print(f"  - ID: {req.id}, Patient: {req.patient_name}, Blood Group: {req.patient_blood_group}")
        print(f"    Hospital: {req.hospital_name}, Priority: {req.priority}")
        print(f"    Current status: {req.status}, Verification: {req.verification_status}")
    
    # Update them
    print(f"\n🔧 Updating {count} request(s)...")
    updated = wrong_status_requests.update(status='pending')
    
    print(f"✅ Successfully updated {updated} request(s)!")
    print("   New status: 'pending'")
    print("   These requests will now appear in the admin verification page.")
    
    # Show all pending requests
    print("\n📋 All pending requests now:")
    pending_requests = BloodRequest.objects.filter(status='pending')
    for req in pending_requests:
        print(f"  - ID: {req.id}, Patient: {req.patient_name}, Status: {req.status}")

if __name__ == '__main__':
    fix_request_status()
