from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import RegexValidator
from auditlog.registry import auditlog
import secrets

class User(AbstractUser):
    """Extended User model for blood donation platform"""
    
    USER_TYPE_CHOICES = [
        ('donor', 'Blood Donor'),
        ('hospital', 'Hospital Representative'),
        ('admin', 'System Administrator'),
    ]
    
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A Positive'),
        ('A-', 'A Negative'),
        ('B+', 'B Positive'),
        ('B-', 'B Negative'),
        ('AB+', 'AB Positive'),
        ('AB-', 'AB Negative'),
        ('O+', 'O Positive'),
        ('O-', 'O Negative'),
    ]
    
    # Core fields
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='donor')
    phone_number = models.CharField(
        max_length=15,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Enter a valid phone number.')],
        blank=True,
        null=True
    )
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, blank=True, null=True, db_index=True)
    date_of_birth = models.DateField(blank=True, null=True)
    last_donation_date = models.DateField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    privacy_level = models.CharField(
        max_length=10,
        choices=[('public', 'Public'), ('private', 'Private')],
        default='public'
    )
    theme = models.CharField(
        max_length=10,
        choices=[('dark', 'Dark Mode'), ('light', 'Light Mode')],
        default='dark'
    )
    
    # Location fields
    city = models.CharField(max_length=100, blank=True, db_index=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='India')
    pincode = models.CharField(max_length=10, blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    
    # Medical information
    has_medical_conditions = models.BooleanField(default=False)
    medical_conditions = models.TextField(blank=True)
    last_medical_checkup = models.DateField(blank=True, null=True)
    
    # GDPR compliance fields
    consent_given = models.BooleanField(default=False)
    data_retention_consent = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Profile completion tracking
    profile_completion_seen = models.BooleanField(default=False)  # Track if user has seen progress bar
    last_notification_check = models.DateTimeField(blank=True, null=True)  # Track last notification check
    
    # Trust system and anti-fake measures
    trust_score = models.IntegerField(default=50, help_text="Trust score from 0-100, affects feature access")
    reports_count = models.IntegerField(default=0, help_text="Number of times user has been reported")
    donations_completed = models.IntegerField(default=0, help_text="Number of successful donations")
    is_blocked = models.BooleanField(default=False, help_text="Auto-blocked if too many reports or low trust")
    firebase_uid = models.CharField(max_length=100, blank=True, null=True, help_text="Firebase user ID for real-time features")
    fcm_token = models.CharField(max_length=255, blank=True, null=True, help_text="Firebase Cloud Messaging token")
    
    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"
    
    @property
    def age(self):
        """Calculate user's age based on date of birth"""
        if self.date_of_birth:
            from datetime import date
            today = date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None
    
    @property
    def is_eligible_donor(self):
        """Check if user is eligible to donate blood"""
        if self.user_type != 'donor' or not self.is_verified:
            return False
        
        # Age validation - must be at least 18 years old
        if self.date_of_birth:
            from datetime import date
            today = date.today()
            age = today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
            if age < 18:
                return False
        
        if self.has_medical_conditions:
            return False
            
        if self.last_donation_date:
            try:
                # Handle both date objects and string dates
                from datetime import datetime
                if isinstance(self.last_donation_date, str):
                    last_donation = datetime.strptime(self.last_donation_date, '%Y-%m-%d').date()
                else:
                    last_donation = self.last_donation_date
                
                # Minimum 3 months between donations
                return (timezone.now().date() - last_donation).days >= 90
            except (ValueError, TypeError):
                # If date parsing fails, assume eligible
                return True
        
        return True
    
    @property
    def days_since_last_donation(self):
        """Return days since last donation"""
        if self.last_donation_date:
            try:
                # Handle both date objects and string dates
                if isinstance(self.last_donation_date, str):
                    from datetime import datetime
                    last_donation = datetime.strptime(self.last_donation_date, '%Y-%m-%d').date()
                else:
                    last_donation = self.last_donation_date

                return (timezone.now().date() - last_donation).days
            except (ValueError, TypeError) as e:
                # If date parsing fails, return None
                print(f"Warning: Could not parse last_donation_date '{self.last_donation_date}': {e}")
                return None
        return None

    @property
    def last_active(self):
        """Return last active timestamp from activity logs"""
        try:
            latest_activity = self.activity_logs.filter(action='login').first()
            if latest_activity:
                return latest_activity.timestamp
        except:
            pass
        return None

    @property
    def last_active_ago(self):
        """Return human-readable time since last active"""
        if not self.last_active:
            return "Never"

        from datetime import timedelta
        now = timezone.now()
        diff = now - self.last_active

        if diff < timedelta(minutes=1):
            return "Just now"
        elif diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff < timedelta(days=7):
            days = diff.days
            return f"{days} day{'s' if days > 1 else ''} ago"
        elif diff < timedelta(days=30):
            weeks = diff.days // 7
            return f"{weeks} week{'s' if weeks > 1 else ''} ago"
        else:
            months = diff.days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"

    def get_profile_completion(self):
        """Calculate profile completion percentage"""
        total_fields = 10
        completed_fields = 0
        
        # Check basic fields
        if self.first_name:
            completed_fields += 1
        if self.last_name:
            completed_fields += 1
        if self.email:
            completed_fields += 1
        if self.phone_number:
            completed_fields += 1
        if self.blood_group:
            completed_fields += 1
        if self.date_of_birth:
            completed_fields += 1
        if self.city:
            completed_fields += 1
        if self.state:
            completed_fields += 1
        if self.pincode:
            completed_fields += 1
        
        # Check profile photo
        try:
            if hasattr(self, 'donor_profile') and self.donor_profile.profile_photo:
                completed_fields += 1
        except:
            pass
        
        percentage = int((completed_fields / total_fields) * 100)
        return {
            'percentage': percentage,
            'completed': completed_fields,
            'total': total_fields,
            'is_complete': percentage >= 80  # Consider 80%+ as complete
        }

class PasswordResetOTP(models.Model):
    """Model to store password reset OTP information"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_otps')
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"OTP for {self.user.username} - Verified: {self.is_verified}"
    
    @property
    def is_expired(self):
        """Check if OTP is expired (5 minutes)"""
        return (timezone.now() - self.created_at).total_seconds() > 300  # 5 minutes
    
    @classmethod
    def generate_otp(cls, user):
        """Generate a new 6-digit OTP for user"""
        # Delete any existing unverified OTPs for this user
        cls.objects.filter(user=user, is_verified=False).delete()
        
        # Generate secure 6-digit OTP
        otp = ''.join(secrets.choice("0123456789") for _ in range(6))
        
        # Create new OTP record
        return cls.objects.create(user=user, otp=otp)
    
    def verify_otp(self, entered_otp):
        """Verify OTP and handle attempts"""
        if self.is_verified:
            return False, "OTP already used"
        
        if self.is_expired:
            return False, "OTP expired"
        
        if self.attempts >= 5:
            return False, "Maximum attempts exceeded"
        
        self.attempts += 1
        self.save()
        
        if self.otp == entered_otp:
            self.is_verified = True
            self.save()
            return True, "OTP verified successfully"
        
        return False, "Invalid OTP"


class LoginOTP(models.Model):
    """Model to store login OTP for two-factor authentication"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_otps')
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"Login OTP for {self.user.username} - Verified: {self.is_verified}"
    
    @property
    def is_expired(self):
        """Check if OTP is expired (10 minutes for login)"""
        return (timezone.now() - self.created_at).total_seconds() > 600  # 10 minutes
    
    @classmethod
    def generate_otp(cls, user, ip_address=None, user_agent=None):
        """Generate a new 6-digit OTP for login"""
        # Delete any existing unverified OTPs for this user
        cls.objects.filter(user=user, is_verified=False).delete()
        
        # Generate secure 6-digit OTP
        otp = ''.join(secrets.choice("0123456789") for _ in range(6))
        
        # Create new OTP record
        return cls.objects.create(
            user=user, 
            otp=otp,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def verify_otp(self, entered_otp):
        """Verify OTP and handle attempts"""
        if self.is_verified:
            return False, "OTP already used"
        
        if self.is_expired:
            return False, "OTP expired"
        
        if self.attempts >= 5:
            return False, "Maximum attempts exceeded"
        
        self.attempts += 1
        self.save()
        
        if self.otp == entered_otp:
            self.is_verified = True
            self.save()
            return True, "OTP verified successfully"
        
        return False, "Invalid OTP"

# Audit logging for compliance
auditlog.register(User)
auditlog.register(PasswordResetOTP)
auditlog.register(LoginOTP)
auditlog.register(DonorRating)
auditlog.register(Hospital)
auditlog.register(HospitalStaff)


class NotificationSettings(models.Model):
    """User notification preferences and settings"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_settings')
    
    # Blood request alerts
    blood_request_alerts = models.BooleanField(default=True)
    emergency_alerts = models.BooleanField(default=True)
    nearby_donation_requests = models.BooleanField(default=True)
    donation_reminders = models.BooleanField(default=True)
    chat_notifications = models.BooleanField(default=True)
    system_updates = models.BooleanField(default=False)
    
    # Notification channels
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    push_notifications = models.BooleanField(default=True)
    
    # Quiet hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(default='23:00:00')  # 11 PM
    quiet_hours_end = models.TimeField(default='06:00:00')    # 6 AM
    
    # Search radius (in km)
    search_radius_km = models.IntegerField(default=25, choices=[
        (5, '5 km'),
        (10, '10 km'),
        (25, '25 km'),
        (50, '50 km'),
        (100, '100 km'),
    ])
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Notification Settings'
        verbose_name_plural = 'Notification Settings'
    
    def __str__(self):
        return f"Notification Settings for {self.user.username}"
    
    def is_quiet_hours(self):
        """Check if current time is within quiet hours"""
        if not self.quiet_hours_enabled:
            return False
        
        from datetime import datetime
        now = datetime.now().time()
        
        # Handle quiet hours that cross midnight
        if self.quiet_hours_start > self.quiet_hours_end:
            return now >= self.quiet_hours_start or now <= self.quiet_hours_end
        else:
            return self.quiet_hours_start <= now <= self.quiet_hours_end


class PrivacySettings(models.Model):
    """User privacy and visibility settings"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='privacy_settings')
    
    # Profile visibility
    profile_visibility = models.CharField(
        max_length=30,
        choices=[
            ('public', 'Public - Everyone can see'),
            ('donors_only', 'Donors Only'),
            ('private', 'Private - Hidden'),
        ],
        default='public'
    )
    
    # Contact info visibility
    show_phone_number = models.BooleanField(default=False)
    show_email = models.BooleanField(default=False)
    show_last_donation_date = models.BooleanField(default=False)
    show_location = models.BooleanField(default=True)
    
    # Anonymous mode
    anonymous_mode = models.BooleanField(default=False)
    
    # Location sharing
    location_sharing_enabled = models.BooleanField(default=True)
    live_location_during_emergency = models.BooleanField(default=True)
    
    # Communication
    enable_chat_requests = models.BooleanField(default=True)
    blocked_users = models.ManyToManyField(User, blank=True, related_name='blocked_by')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Privacy Settings'
        verbose_name_plural = 'Privacy Settings'
    
    def __str__(self):
        return f"Privacy Settings for {self.user.username}"


class DonorProfile(models.Model):
    """Extended donor profile with availability and health information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='donor_profile')

    # Profile photo
    profile_photo = models.ImageField(
        upload_to='profile_photos/',
        blank=True,
        null=True,
        help_text="Upload your profile photo"
    )

    # Availability status
    AVAILABILITY_CHOICES = [
        ('available', 'Available to Donate ✅'),
        ('not_available', 'Not Available ❌'),
        ('busy', 'Busy ⏳'),
        ('temporarily_deferred', 'Temporarily Deferred 🚫'),
    ]

    availability_status = models.CharField(
        max_length=25,
        choices=AVAILABILITY_CHOICES,
        default='available'
    )

    # Donation tracking
    total_donations = models.IntegerField(default=0)
    last_donation_location = models.CharField(max_length=200, blank=True)
    next_eligible_date = models.DateField(blank=True, null=True)
    
    # Health information
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    has_recent_illness = models.BooleanField(default=False)
    recent_illness_details = models.TextField(blank=True)
    medical_restrictions = models.TextField(blank=True)
    
    # Auto-calculated fields
    auto_disable_until = models.DateField(blank=True, null=True)
    
    # Badges and achievements
    badges = models.JSONField(default=list, blank=True)
    
    # Emergency contact
    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True)
    emergency_contact_relation = models.CharField(max_length=100, blank=True)
    
    # Preferences
    preferred_donation_centers = models.JSONField(default=list, blank=True)
    donation_frequency_preference = models.CharField(
        max_length=20,
        choices=[
            ('regular', 'Regular (Every 3 months)'),
            ('occasional', 'Occasional'),
            ('emergency_only', 'Emergency Only'),
        ],
        default='regular'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Donor Profile'
        verbose_name_plural = 'Donor Profiles'
    
    def __str__(self):
        return f"Donor Profile: {self.user.username}"
    
    def calculate_next_eligible_date(self):
        """Auto-calculate next eligible donation date based on gender and last donation"""
        if not self.user.last_donation_date:
            return None
        
        from datetime import timedelta
        # Standard 90 days gap (can be adjusted based on gender if needed)
        gap_days = 90
        
        try:
            from datetime import datetime
            last_donation = self.user.last_donation_date
            if isinstance(last_donation, str):
                last_donation = datetime.strptime(last_donation, '%Y-%m-%d').date()
            
            self.next_eligible_date = last_donation + timedelta(days=gap_days)
            self.save()
            return self.next_eligible_date
        except (ValueError, TypeError):
            return None
    
    def update_availability_based_on_eligibility(self):
        """Auto-disable availability if not eligible"""
        if not self.user.is_eligible_donor:
            self.availability_status = 'not_available'
            if self.user.last_donation_date:
                self.calculate_next_eligible_date()
            self.save()


class UserReport(models.Model):
    """Model for reporting users for fake/scam behavior"""
    
    REPORT_REASON_CHOICES = [
        ('fake_profile', 'Fake Profile'),
        ('spam', 'Spam Messages'),
        ('inappropriate', 'Inappropriate Behavior'),
        ('scam', 'Scam Attempt'),
        ('harassment', 'Harassment'),
        ('other', 'Other'),
    ]
    
    REPORT_STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('investigating', 'Under Investigation'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    reported_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_received')
    reason = models.CharField(max_length=50, choices=REPORT_REASON_CHOICES)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=REPORT_STATUS_CHOICES, default='pending')
    is_resolved = models.BooleanField(default=False)
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        unique_together = ['reporter', 'reported_user']  # One user can report another only once
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['reported_user', 'status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Report: {self.reporter.username} -> {self.reported_user.username} ({self.reason})"
    
    def save(self, *args, **kwargs):
        # Auto-increment reports_count on reported user
        if not self.id:  # New report
            self.reported_user.reports_count += 1
            self.reported_user.save()
            
            # Auto-block if 3+ reports
            if self.reported_user.reports_count >= 3:
                self.reported_user.is_blocked = True
                self.reported_user.trust_score = max(0, self.reported_user.trust_score - 50)
                self.reported_user.save()
            
            # Reduce trust score
            self.reported_user.trust_score = max(0, self.reported_user.trust_score - 10)
            self.reported_user.save()
        
        super().save(*args, **kwargs)


class UserActivityLog(models.Model):
    """Track user login activity and device management"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('password_change', 'Password Changed'),
        ('settings_update', 'Settings Updated'),
        ('profile_update', 'Profile Updated'),
    ]
    
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    device_info = models.CharField(max_length=200, blank=True)
    location_info = models.CharField(max_length=200, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()} at {self.timestamp}"


class FavoriteDonor(models.Model):
    """Track donors saved/favorited by users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_donors')
    favorite_donor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, help_text="Personal notes about this donor")

    class Meta:
        unique_together = ['user', 'favorite_donor']
        ordering = ['-created_at']
        verbose_name = 'Favorite Donor'
        verbose_name_plural = 'Favorite Donors'

    def __str__(self):
        return f"{self.user.username} → {self.favorite_donor.username}"


class Follow(models.Model):
    """Track user follows (Instagram-style social connections)"""
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')
        ordering = ['-created_at']
        verbose_name = 'Follow'
        verbose_name_plural = 'Follows'

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


class DonorRating(models.Model):
    """Donor rating system for building trust"""
    
    RATING_CHOICES = [
        (1, 'Poor'),
        (2, 'Fair'),
        (3, 'Good'),
        (4, 'Very Good'),
        (5, 'Excellent'),
    ]
    
    donor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_ratings')
    rater = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_ratings')
    blood_request = models.ForeignKey('blood_requests_app.BloodRequest', on_delete=models.CASCADE, related_name='ratings', null=True, blank=True)
    
    rating = models.IntegerField(choices=RATING_CHOICES)
    review = models.TextField(blank=True, help_text="Optional review/comments")
    
    # Rating categories
    punctuality = models.IntegerField(choices=RATING_CHOICES, default=5, help_text="Arrived on time")
    professionalism = models.IntegerField(choices=RATING_CHOICES, default=5, help_text="Professional behavior")
    communication = models.IntegerField(choices=RATING_CHOICES, default=5, help_text="Communication quality")
    
    is_verified = models.BooleanField(default=False, help_text="Verified by hospital staff")
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_ratings')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['donor', 'rater', 'blood_request']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['donor', '-rating']),
            models.Index(fields=['blood_request']),
        ]
    
    def __str__(self):
        return f"{self.rater.username} rated {self.donor.username}: {self.rating}/5"
    
    @property
    def average_rating(self):
        """Calculate average of all rating categories"""
        return (self.rating + self.punctuality + self.professionalism + self.communication) / 4
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Update donor's trust score based on ratings
        self.update_donor_trust_score()
    
    def update_donor_trust_score(self):
        """Update donor's trust score based on average rating"""
        from django.db.models import Avg
        
        avg_rating = DonorRating.objects.filter(donor=self.donor).aggregate(
            avg=Avg('rating')
        )['avg'] or 3
        
        # Map rating (1-5) to trust score (0-100)
        # Rating 3 = 50, Rating 5 = 100, Rating 1 = 0
        new_trust_score = int((avg_rating / 5) * 100)
        
        # Blend with existing trust score (70% new, 30% old)
        self.donor.trust_score = int((new_trust_score * 0.7) + (self.donor.trust_score * 0.3))
        self.donor.save(update_fields=['trust_score'])


class Hospital(models.Model):
    """Hospital model for verified blood donation centers"""
    
    HOSPITAL_TYPE_CHOICES = [
        ('government', 'Government Hospital'),
        ('private', 'Private Hospital'),
        ('ngo', 'NGO Blood Bank'),
        ('blood_bank', 'Blood Bank'),
    ]
    
    VERIFICATION_STATUS_CHOICES = [
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]
    
    name = models.CharField(max_length=200)
    hospital_type = models.CharField(max_length=20, choices=HOSPITAL_TYPE_CHOICES, default='private')
    license_number = models.CharField(max_length=100, unique=True, help_text="Hospital license/registration number")
    
    # Location
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    
    # Contact
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    emergency_contact = models.CharField(max_length=15, blank=True)
    
    # Blood bank details
    has_blood_bank = models.BooleanField(default=True)
    blood_groups_available = models.JSONField(default=list, help_text="List of available blood groups")
    
    # Verification
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS_CHOICES, default='pending')
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_hospitals')
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_documents = models.FileField(upload_to='hospital_documents/', blank=True, null=True)
    
    # Statistics
    total_donations_processed = models.IntegerField(default=0)
    active_requests = models.IntegerField(default=0)
    
    # Trust score
    trust_score = models.IntegerField(default=50, help_text="Trust score from 0-100")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-trust_score', '-created_at']
        indexes = [
            models.Index(fields=['city', 'verification_status']),
            models.Index(fields=['trust_score']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.city})"
    
    @property
    def is_verified(self):
        return self.verification_status == 'verified'


class HospitalStaff(models.Model):
    """Hospital staff members who can create verified blood requests"""
    
    ROLE_CHOICES = [
        ('admin', 'Hospital Admin'),
        ('doctor', 'Doctor'),
        ('nurse', 'Nurse'),
        ('coordinator', 'Blood Donation Coordinator'),
    ]
    
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='staff')
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='hospital_staff_profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='coordinator')
    employee_id = models.CharField(max_length=50, unique=True)
    department = models.CharField(max_length=100, blank=True)
    
    # Permissions
    can_create_requests = models.BooleanField(default=True)
    can_approve_requests = models.BooleanField(default=False)
    can_manage_inventory = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['hospital', 'user']
    
    def __str__(self):
        return f"{self.user.username} - {self.hospital.name} ({self.get_role_display()})"


# Auto-create settings when user is created
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_settings(sender, instance, created, **kwargs):
    """Automatically create settings profiles for new users"""
    if created:
        NotificationSettings.objects.create(user=instance)
        PrivacySettings.objects.create(user=instance)
        if instance.user_type == 'donor':
            DonorProfile.objects.create(user=instance)
