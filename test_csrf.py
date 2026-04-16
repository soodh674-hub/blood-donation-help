"""
CSRF Token Test - Verify CSRF configuration is working correctly
Run this to test if CSRF tokens are properly configured.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blood_donation.settings')
django.setup()

from django.conf import settings
from django.middleware.csrf import get_token
from django.test import RequestFactory

def test_csrf_configuration():
    """Test CSRF configuration settings"""
    
    print("=" * 70)
    print("🔍 CSRF TOKEN CONFIGURATION TEST")
    print("=" * 70)
    print()
    
    # Test 1: Check CSRF settings
    print("📋 Checking CSRF Settings...")
    print("-" * 70)
    
    csrf_settings = {
        'CSRF_COOKIE_NAME': settings.CSRF_COOKIE_NAME,
        'CSRF_COOKIE_HTTPONLY': settings.CSRF_COOKIE_HTTPONLY,
        'CSRF_COOKIE_SECURE': settings.CSRF_COOKIE_SECURE,
        'CSRF_COOKIE_SAMESITE': settings.CSRF_COOKIE_SAMESITE,
        'CSRF_HEADER_NAME': settings.CSRF_HEADER_NAME,
    }
    
    all_passed = True
    
    for setting, value in csrf_settings.items():
        print(f"✅ {setting}: {value}")
    
    print()
    
    # Test 2: Validate critical settings
    print("✓ Validating Critical Settings...")
    print("-" * 70)
    
    # CSRF_COOKIE_HTTPONLY must be False
    if settings.CSRF_COOKIE_HTTPONLY == False:
        print("✅ CSRF_COOKIE_HTTPONLY is False (JavaScript can read token)")
    else:
        print("❌ CSRF_COOKIE_HTTPONLY is True (JavaScript CANNOT read token)")
        print("   This will cause AJAX CSRF errors!")
        all_passed = False
    
    # CSRF_COOKIE_NAME should be 'csrftoken'
    if settings.CSRF_COOKIE_NAME == 'csrftoken':
        print("✅ CSRF_COOKIE_NAME is 'csrftoken' (correct)")
    else:
        print(f"⚠️  CSRF_COOKIE_NAME is '{settings.CSRF_COOKIE_NAME}' (expected 'csrftoken')")
    
    # CSRF_HEADER_NAME should be 'HTTP_X_CSRFTOKEN'
    if settings.CSRF_HEADER_NAME == 'HTTP_X_CSRFTOKEN':
        print("✅ CSRF_HEADER_NAME is 'HTTP_X_CSRFTOKEN' (correct)")
    else:
        print(f"⚠️  CSRF_HEADER_NAME is '{settings.CSRF_HEADER_NAME}'")
    
    print()
    
    # Test 3: Generate a test token
    print("🎫 Testing Token Generation...")
    print("-" * 70)
    
    factory = RequestFactory()
    request = factory.get('/test/')
    
    try:
        token = get_token(request)
        token_length = len(token)
        
        print(f"✅ Token generated successfully")
        print(f"   Token: {token[:20]}... (first 20 chars)")
        print(f"   Length: {token_length} characters")
        
        # Token should be 32-64 characters
        if 32 <= token_length <= 64:
            print(f"✅ Token length is valid (32-64 chars)")
        else:
            print(f"❌ Token length is invalid! Expected 32-64, got {token_length}")
            all_passed = False
            
    except Exception as e:
        print(f"❌ Failed to generate token: {e}")
        all_passed = False
    
    print()
    
    # Test 4: Check CSRF_TRUSTED_ORIGINS
    print("🌐 Checking CSRF_TRUSTED_ORIGINS...")
    print("-" * 70)
    
    if hasattr(settings, 'CSRF_TRUSTED_ORIGINS'):
        origins = settings.CSRF_TRUSTED_ORIGINS
        print(f"✅ CSRF_TRUSTED_ORIGINS is configured")
        print(f"   Trusted origins: {origins}")
    else:
        print("⚠️  CSRF_TRUSTED_ORIGINS not explicitly set (using Django defaults)")
    
    print()
    
    # Test 5: Check environment
    print("🔧 Environment Check...")
    print("-" * 70)
    
    print(f"   DEBUG: {settings.DEBUG}")
    print(f"   IS_RENDER: {settings.IS_RENDER}")
    
    if settings.IS_RENDER:
        if settings.CSRF_COOKIE_SECURE:
            print("✅ CSRF_COOKIE_SECURE is True (production HTTPS)")
        else:
            print("⚠️  CSRF_COOKIE_SECURE is False in production (should be True)")
    else:
        if not settings.CSRF_COOKIE_SECURE:
            print("✅ CSRF_COOKIE_SECURE is False (development HTTP)")
        else:
            print("⚠️  CSRF_COOKIE_SECURE is True in development (may cause issues)")
    
    print()
    
    # Final summary
    print("=" * 70)
    if all_passed:
        print("✅ ALL CSRF TESTS PASSED!")
        print()
        print("Your CSRF configuration is correct.")
        print("AJAX requests should work without CSRF errors.")
    else:
        print("❌ SOME TESTS FAILED!")
        print()
        print("Please review the errors above.")
        print("See CSRF_FIX.md for troubleshooting.")
    print("=" * 70)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    try:
        exit_code = test_csrf_configuration()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
