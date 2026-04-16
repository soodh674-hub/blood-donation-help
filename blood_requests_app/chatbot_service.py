"""
Blood Donation Chatbot Service
Provides intelligent responses to common queries about blood donation
"""

import re
from datetime import datetime, timedelta
from django.utils import timezone


class BloodDonationChatbot:
    """AI-powered chatbot for blood donation platform"""
    
    def __init__(self):
        self.context = {}
        self.conversation_history = []
        
        # Define response patterns
        self.patterns = {
            # Blood donation eligibility
            r'(can|eligible|who).*donat(e|ing)': self.handle_eligibility,
            r'(age|old).*donat(e|ing)': self.handle_age_requirement,
            r'(weight|weigh).*donat(e|ing)': self.handle_weight_requirement,
            r'(medical|condition|disease).*donat(e|ing)': self.handle_medical_conditions,
            
            # Blood types
            r'(blood.*type|blood.*group|which.*blood)': self.handle_blood_types,
            r'(universal|o[-+]?)': self.handle_universal_donor,
            
            # Donation process
            r'(how.*donat(e|ing)|process|procedure)': self.handle_donation_process,
            r'(long|time|duration).*donat(e|ing)': self.handle_donation_duration,
            r'(pain|hurt).*donat(e|ing)': self.handle_pain_concerns,
            r'(after|side.*effect|recover)': self.handle_after_effects,
            
            # Location and timing
            r'(where|near|location|center)': self.handle_location,
            r'(when|time|hour|open)': self.handle_timing,
            
            # Emergency requests
            r'(emergency|urgent|critical)': self.handle_emergency,
            r'(create|make|new).*request': self.handle_create_request,
            
            # Account and profile
            r'(profile|account|update|change)': self.handle_profile,
            r'(login|signin|password)': self.handle_account_issues,
            
            # Matching and finding donors
            r'(find|search|match).*donor': self.handle_find_donor,
            r'(track|status).*request': self.handle_track_request,
            
            # Health and safety
            r'(safe|safety|risk|hiv|aids)': self.handle_safety,
            r'(test|screen|check)': self.handle_testing,
            
            # General information
            r'(benefit|why|good|help)': self.handle_benefits,
            r'(contact|help|support)': self.handle_contact,
            
            # Greetings
            r'(hello|hi|hey|good)': self.handle_greeting,
            r'(thank|thanks)': self.handle_thanks,
            r'(bye|goodbye)': self.handle_goodbye,
        }
    
    def get_response(self, user_message, user_context=None):
        """
        Get chatbot response based on user message
        
        Args:
            user_message: The user's input message
            user_context: Optional context about the user (blood type, location, etc.)
        
        Returns:
            Dictionary with response and metadata
        """
        self.context = user_context or {}
        self.conversation_history.append({
            'role': 'user',
            'message': user_message,
            'timestamp': timezone.now()
        })
        
        message_lower = user_message.lower()
        
        # Try to match patterns
        for pattern, handler in self.patterns.items():
            if re.search(pattern, message_lower):
                response = handler(user_message)
                self.conversation_history.append({
                    'role': 'bot',
                    'message': response,
                    'timestamp': timezone.now()
                })
                return {
                    'response': response,
                    'confidence': 'high',
                    'suggestions': self.get_suggestions(pattern)
                }
        
        # Default response
        default_response = self.handle_default(user_message)
        self.conversation_history.append({
            'role': 'bot',
            'message': default_response,
            'timestamp': timezone.now()
        })
        return {
            'response': default_response,
            'confidence': 'low',
            'suggestions': self.get_general_suggestions()
        }
    
    def handle_eligibility(self, message):
        return """To be eligible for blood donation, you must:
        
✓ Be between 18-65 years old
✓ Weigh at least 50 kg (110 lbs)
✓ Be in good general health
✓ Have hemoglobin level ≥ 12.5 g/dL
✓ Not have donated blood in the last 3 months

Would you like to know about any specific eligibility criteria?"""
    
    def handle_age_requirement(self, message):
        return """You must be between 18 and 65 years old to donate blood in most countries.
        
• 18-60: Can donate regularly (every 3 months)
• 60-65: Can donate with doctor's approval
• Under 18: Not eligible for donation
• Over 65: Generally not recommended

First-time donors should be 18-60 years old."""
    
    def handle_weight_requirement(self, message):
        return """You must weigh at least 50 kg (110 lbs) to donate blood.
        
• Under 50 kg: Not eligible
• 50-60 kg: Can donate 350 ml
• Over 60 kg: Can donate 450 ml

The amount donated is safe and won't affect your health."""
    
    def handle_medical_conditions(self, message):
        return """Certain medical conditions may temporarily or permanently prevent donation:

**Temporary deferral (1 year or less):**
• Recent surgery or vaccination
• Pregnancy or recent childbirth
• Recent tattoo or piercing
• Certain medications

**Permanent deferral:**
• HIV/AIDS
• Hepatitis B or C
• Cancer (treated within last 5 years)
• Heart disease
• Chronic kidney disease

Please consult a doctor if you have specific concerns."""
    
    def handle_blood_types(self, message):
        return """There are 8 main blood types: A+, A-, B+, B-, AB+, AB-, O+, O-

**Compatibility for RECEIVING blood:**
• A+: Can receive A+, A-, O+, O-
• A-: Can receive A-, O-
• B+: Can receive B+, B-, O+, O-
• B-: Can receive B-, O-
• AB+: Can receive ALL types (Universal Recipient)
• AB-: Can receive A-, B-, AB-, O-
• O+: Can receive O+, O-
• O-: Can receive O- only (Universal Donor)

Your blood type is determined by genetics and cannot be changed."""
    
    def handle_universal_donor(self, message):
        return """O- (O Negative) is the universal donor type.

**Why O- is special:**
• Can donate to ANY blood type
• Critical for emergencies
• Only 7% of the population has O-
• Always in high demand

If you have O- blood, your donation is especially valuable and can save lives in emergency situations."""
    
    def handle_donation_process(self, message):
        return """The blood donation process takes about 30-45 minutes:

**Steps:**
1. **Registration** (5 min) - Fill out form and show ID
2. **Health screening** (10 min) - Check hemoglobin, blood pressure, temperature
3. **Donation** (10-15 min) - Actual blood collection
4. **Refreshment** (10 min) - Rest and have snacks

**What to bring:**
• Valid government ID
• List of medications (if any)
• Eat a healthy meal beforehand
• Drink plenty of water

The process is safe, sterile, and performed by trained professionals."""
    
    def handle_donation_duration(self, message):
        return """The actual blood donation takes 10-15 minutes.

**Total time at center:** 30-45 minutes
• Registration: 5 minutes
• Screening: 10 minutes
• Donation: 10-15 minutes
• Recovery: 10 minutes

You can donate whole blood every 3 months (up to 4 times per year). Platelet donation can be done more frequently (every 2 weeks)."""
    
    def handle_pain_concerns(self, message):
        return """Blood donation is generally not painful.

**What to expect:**
• A small pinch when the needle is inserted (like a quick bee sting)
• Mild discomfort during donation
• No pain after the needle is removed

**Tips to minimize discomfort:**
• Stay relaxed
• Don't look at the needle
• Squeeze a stress ball during donation
• Inform staff if you feel any pain

The staff are trained to make the experience as comfortable as possible."""
    
    def handle_after_effects(self, message):
        return """Most people feel fine after donating. Here's what to expect:

**Normal side effects:**
• Mild fatigue for a few hours
• Slight dizziness (avoid driving immediately)
• Small bruise at needle site
• Feeling thirsty

**Recovery tips:**
• Drink extra water for 24-48 hours
• Avoid heavy exercise for 24 hours
• Eat iron-rich foods
• Keep the bandage on for 4-6 hours

**Contact a doctor if:**
• Dizziness persists for more than a day
• Severe bruising or bleeding
• Fever or other symptoms"""
    
    def handle_location(self, message):
        """Handle location queries - use user context if available"""
        if self.context.get('city'):
            return f"""Based on your location ({self.context.get('city')}), you can:

1. Use our **Find Donors** feature to locate nearby donors
2. Check blood banks in your area
3. Create a blood request if you need blood urgently

You can also enable location services in your profile for better matching.

Would you like help finding a donor or blood bank near you?"""
        return """To find donation centers or donors near you:

1. **Enable location services** in your profile
2. Use the **Find Donors** feature on the homepage
3. Check the **Blood Banks** section in your area

The platform can match you with donors within your specified search radius (default: 50 km).

Would you like me to help you set up your location preferences?"""
    
    def handle_timing(self, message):
        return """Most blood donation centers operate during these hours:

**Typical hours:**
• Monday-Friday: 9:00 AM - 6:00 PM
• Saturday: 9:00 AM - 2:00 PM
• Sunday: Closed (varies by location)

**Best times to donate:**
• Morning appointments (less crowded)
• Mid-week (Tuesday-Thursday)
• Avoid peak hours (12-2 PM)

**Emergency requests:** Available 24/7 through our platform

I recommend calling ahead to confirm hours at your local center."""
    
    def handle_emergency(self, message):
        return """**EMERGENCY BLOOD REQUEST**

If you need blood urgently:

1. **Create an Emergency Request** immediately through our platform
2. Mark it as "Emergency" priority
3. Provide accurate location and contact information
4. The system will notify nearby donors instantly

**For critical emergencies:**
• Call emergency services (108/112)
• Contact the nearest hospital directly
• Use our platform to find O- donors (universal donors)

The system will prioritize your request and send real-time notifications to all eligible donors in your area.

Would you like help creating an emergency request now?"""
    
    def handle_create_request(self, message):
        return """To create a blood request:

1. Go to **Create Request** in the menu
2. Fill in patient details (name, blood type, units needed)
3. Provide hospital and location information
4. Set urgency level (Normal, Urgent, or Emergency)
5. Add contact information for donors

**Required information:**
• Patient's blood type
• Number of units needed
• Hospital name and address
• Contact person and phone number
• Required date

The system will automatically match you with compatible donors and send notifications.

Would you like step-by-step guidance for creating a request?"""
    
    def handle_profile(self, message):
        return """You can manage your profile in the Settings section:

**Profile features:**
• Update personal information
• Change blood type (if not verified)
• Set availability status
• Manage notification preferences
• Configure privacy settings
• Enable/disable anonymous mode

**To update your profile:**
1. Go to **My Profile** from the dashboard
2. Click **Edit Profile**
3. Make changes and save

Your profile helps match you with compatible blood requests or donors.

What would you like to update in your profile?"""
    
    def handle_account_issues(self, message):
        return """For account-related issues:

**Login problems:**
• Use "Forgot Password" to reset
• Check your email for verification
• Ensure you're using the correct username

**Profile issues:**
• Contact support through the Help section
• Email: support@bloodlife.com
• Include your username and issue description

**Account deletion:**
• Go to Settings → Account
• Click "Delete Account"
• This action cannot be undone

For technical issues, please contact our support team with detailed information about the problem."""
    
    def handle_find_donor(self, message):
        return """To find compatible donors:

1. Go to **Find Donors** on the homepage
2. Filter by blood type (if needed)
3. Set your search radius (default: 50 km)
4. View donor profiles and availability

**Matching criteria:**
• Blood type compatibility
• Geographic proximity
• Donor availability status
• Last donation date (must be ≥ 3 months ago)

**Tips:**
• Contact multiple donors
• Provide clear request details
• Be respectful of donor's time
• Follow up politely

The platform shows donors who are eligible and available. Would you like help filtering donors by specific criteria?"""
    
    def handle_track_request(self, message):
        return """To track your blood request:

1. Go to **My Requests** from the dashboard
2. Click on the request you want to track
3. View real-time status and donor responses

**Request statuses:**
• **Pending** - Waiting for donor responses
• **Active** - Donor has responded
• **Fulfilled** - Blood donation completed
• **Cancelled** - Request cancelled

**Tracking features:**
• Real-time donor location (if enabled)
• Chat with donors
• View donor profiles
• Update request details

You'll receive notifications when donors respond to your request."""
    
    def handle_safety(self, message):
        return """Blood donation is extremely safe. Here's why:

**Sterile equipment:**
• New, sterile needle for every donor
• Single-use collection bags
• No risk of contamination

**Screening process:**
• Donor health screening
• Blood testing for diseases
• Confidential medical history

**Disease testing:**
• HIV/AIDS
• Hepatitis B and C
• Syphilis
• Malaria (in endemic areas)

**Your safety:**
• Professional medical staff
• Post-donation care
• Follow-up if needed

The risk of infection from donating blood is virtually zero. All equipment is disposable and never reused."""
    
    def handle_testing(self, message):
        return """Every donated blood unit undergoes comprehensive testing:

**Tests performed:**
• Blood type and Rh factor
• HIV (1 & 2)
• Hepatitis B & C
• Syphilis
• Malaria (in endemic areas)
• Hemoglobin level

**If issues are found:**
• Donor is notified confidentially
• Blood unit is discarded
• Donor may be temporarily/permanently deferred
• Referral to healthcare provider

**Confidentiality:**
• All test results are private
• Only shared with the donor
• Used to ensure blood safety

Testing ensures safe blood for recipients and protects donor health."""
    
    def handle_benefits(self, message):
        return """Donating blood has many benefits:

**For recipients:**
• Saves lives
• Helps surgery patients
• Supports cancer treatment
• Aids accident victims

**For donors:**
• Free health screening
• Reduced risk of heart disease
• Burns calories (~650 calories per donation)
• Sense of helping others
• Community impact

**Social impact:**
• One donation can save up to 3 lives
• Helps maintain blood supply
• Supports healthcare system
• Encourages others to donate

Every 2 seconds, someone needs blood. Your donation makes a real difference."""
    
    def handle_contact(self, message):
        return """**Contact BloodLife Support:**

**Email:** support@bloodlife.com
**Phone:** +91-1800-BLOOD (toll-free)
**Hours:** 9 AM - 6 PM IST

**For emergencies:**
• Use the in-app emergency feature
• Call emergency services: 108/112
• Contact nearest hospital directly

**Online support:**
• Help section in the app
• FAQ on our website
• Community forum
• Social media channels

We typically respond within 24 hours for non-urgent queries. Emergency requests are prioritized.

How can I help you today?"""
    
    def handle_greeting(self, message):
        greetings = [
            "Hello! I'm your BloodLife assistant. How can I help you today?",
            "Hi there! I can help with blood donation questions, finding donors, or creating requests. What would you like to know?",
            "Welcome! I'm here to assist with anything related to blood donation. What's on your mind?"
        ]
        return greetings[hash(message) % len(greetings)]
    
    def handle_thanks(self, message):
        responses = [
            "You're welcome! Is there anything else I can help you with?",
            "Happy to help! Let me know if you have more questions.",
            "Anytime! Don't hesitate to ask if you need anything else."
        ]
        return responses[hash(message) % len(responses)]
    
    def handle_goodbye(self, message):
        return """Goodbye! Remember:

• One donation can save up to 3 lives
• You can donate every 3 months
• Stay healthy and keep helping others

Thank you for using BloodLife. Take care!"""
    
    def handle_default(self, message):
        return """I'm not sure I understand. Here are some things I can help with:

**Blood donation:**
• Eligibility requirements
• Donation process
• After-effects and recovery

**Using the platform:**
• Finding donors
• Creating blood requests
• Tracking requests
• Profile management

**General information:**
• Blood types and compatibility
• Safety and testing
• Location and timing

Try asking about any of these topics, or contact our support team for more help.

What would you like to know?"""
    
    def get_suggestions(self, pattern):
        """Get follow-up suggestions based on matched pattern"""
        suggestions_map = {
            r'(can|eligible).*donat': [
                "What about age requirements?",
                "What medical conditions prevent donation?",
                "How often can I donate?"
            ],
            r'(blood.*type|blood.*group)': [
                "What is a universal donor?",
                "Which blood type can receive any blood?",
                "How is blood type determined?"
            ],
            r'(how.*donat|process)': [
                "How long does it take?",
                "Is it painful?",
                "What should I bring?"
            ],
            r'(emergency|urgent)': [
                "How do I create an emergency request?",
                "What happens after I create a request?",
                "How quickly will donors respond?"
            ],
            r'(find|search).*donor': [
                "How does donor matching work?",
                "Can I filter by location?",
                "How do I contact a donor?"
            ],
        }
        
        for key, suggestions in suggestions_map.items():
            if re.search(key, pattern):
                return suggestions
        
        return self.get_general_suggestions()
    
    def get_general_suggestions(self):
        return [
            "Am I eligible to donate?",
            "How do I find a donor?",
            "What's the donation process?",
            "How do I create a blood request?",
            "Where can I donate?"
        ]


# Singleton instance
chatbot = BloodDonationChatbot()


def get_chatbot_response(message, user_context=None):
    """
    Convenience function to get chatbot response
    
    Args:
        message: User's message
        user_context: Optional user context dict
    
    Returns:
        Response dictionary
    """
    return chatbot.get_response(message, user_context)
