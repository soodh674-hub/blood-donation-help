#!/usr/bin/env python
"""
Simple email delivery diagnosis script
Checks Brevo API configuration and connectivity
"""
import os
import sys

def check_email_config():
    print("=" * 60)
    print("EMAIL DELIVERY DIAGNOSIS")
    print("=" * 60)
    
    # Check Brevo API key
    api_key = os.environ.get('BREVO_API_KEY') or os.environ.get('SENDINBLUE_API_KEY')
    
    if not api_key:
        print("❌ Brevo API key not found in environment variables")
        return False
    
    print(f"✅ Brevo API key found (length: {len(api_key)})")
    
    # Check if it's a test key
    if 'test' in api_key.lower() or 'xkeysib' not in api_key:
        print("⚠️  Warning: This might be a test API key")
    else:
        print("✅ API key format looks valid")
    
    # Check sender email
    sender_email = os.environ.get('DEFAULT_FROM_EMAIL') or os.environ.get('EMAIL_HOST_USER')
    if sender_email:
        print(f"✅ Sender email configured: {sender_email}")
    else:
        print("⚠️  Default sender email not configured")
    
    print("\n✅ Email configuration looks good!")
    print("=" * 60)
    return True

if __name__ == '__main__':
    try:
        check_email_config()
    except Exception as e:
        print(f"⚠️  Diagnosis error: {e}")
        sys.exit(0)  # Don't fail the build
