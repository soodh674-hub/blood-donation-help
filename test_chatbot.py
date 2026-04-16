"""
Test the chatbot API endpoint
Run this to verify the chatbot is working correctly
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blood_donation.settings')
django.setup()

from blood_requests_app.chatbot_service import get_chatbot_response

def test_chatbot():
    """Test chatbot responses"""
    
    print("=" * 70)
    print("🤖 CHATBOT TEST")
    print("=" * 70)
    print()
    
    # Test messages
    test_messages = [
        "Hello",
        "Am I eligible to donate blood?",
        "What is the donation process?",
        "How do I find a donor?",
        "I need blood urgently",
        "What are the benefits of donating blood?",
        "Random question about something else"
    ]
    
    print("Testing chatbot responses...\n")
    
    for i, message in enumerate(test_messages, 1):
        print(f"Test {i}: '{message}'")
        print("-" * 70)
        
        try:
            response = get_chatbot_response(message, {
                'user_id': 1,
                'username': 'testuser',
                'blood_group': 'O+',
            })
            
            print(f"✅ Response received")
            print(f"   Confidence: {response.get('confidence', 'unknown')}")
            print(f"   Response: {response['response'][:100]}...")
            print(f"   Suggestions: {response.get('suggestions', [])}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    print("=" * 70)
    print("✅ CHATBOT TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    test_chatbot()
