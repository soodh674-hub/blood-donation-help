from django.db import models
from django.utils import timezone
from accounts.models import User
from auditlog.registry import auditlog
import logging

logger = logging.getLogger(__name__)


class BloodDonationCamp(models.Model):
    """Blood donation camp management for admin"""
    
    CAMP_STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    venue = models.CharField(max_length=300)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=CAMP_STATUS_CHOICES, default='upcoming')
    target_units = models.IntegerField(default=100)
    collected_units = models.IntegerField(default=0)
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_camps')
    contact_number = models.CharField(max_length=15)
    contact_email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Blood Donation Camp'
        verbose_name_plural = 'Blood Donation Camps'
    
    def __str__(self):
        return f"{self.name} - {self.start_date.strftime('%Y-%m-%d')}"
    
    @property
    def is_active(self):
        now = timezone.now()
        return self.start_date <= now <= self.end_date and self.status == 'ongoing'
    
    @property
    def completion_percentage(self):
        if self.target_units > 0:
            return min(100, (self.collected_units / self.target_units) * 100)
        return 0


class DonorRating(models.Model):
    """Donor rating system for blood donations"""
    
    RATING_CHOICES = [
        (1, 'Poor'),
        (2, 'Fair'),
        (3, 'Good'),
        (4, 'Very Good'),
        (5, 'Excellent'),
    ]
    
    donor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_ratings')
    rater = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_ratings')
    blood_request = models.ForeignKey('BloodRequest', on_delete=models.CASCADE, related_name='donor_ratings')
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['donor', 'rater', 'blood_request']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.rater.username} rated {self.donor.username}: {self.rating}/5"


class BloodRequest(models.Model):
    """Enhanced Blood request with real-time tracking support"""
    
    PRIORITY_CHOICES = [
        ('normal', 'Normal'),
        ('urgent', 'Urgent'),
        ('emergency', 'Emergency'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('active', 'Active - Seeking Donors'),
        ('partially_fulfilled', 'Partially Fulfilled'),
        ('fulfilled', 'Fulfilled'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]
    
    VERIFICATION_STATUS_CHOICES = [
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('under_review', 'Under Review'),
    ]
    
    REQUESTER_TYPE_CHOICES = [
        ('hospital', 'Hospital'),
        ('individual', 'Individual Patient'),
        ('relative', 'Patient Relative'),
    ]
    
    # Core fields
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blood_requests')
    patient_name = models.CharField(max_length=200)
    patient_age = models.IntegerField()
    patient_blood_group = models.CharField(max_length=3)
    required_units = models.IntegerField(default=1)
    fulfilled_units = models.IntegerField(default=0)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS_CHOICES, default='pending')
    requester_type = models.CharField(max_length=10, choices=REQUESTER_TYPE_CHOICES, default='hospital')
    
    # Medical details
    reason = models.TextField()
    required_by = models.DateTimeField()
    medical_certificate = models.FileField(upload_to='medical_certificates/', blank=True, null=True)
    is_critical = models.BooleanField(default=False)
    
    # Location (Enhanced for map integration)
    hospital_name = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='India')
    pincode = models.CharField(max_length=6)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    exact_address = models.TextField(blank=True, help_text="Detailed address for navigation")
    
    # Contact information
    contact_person = models.CharField(max_length=100)
    contact_phone = models.CharField(max_length=15)
    contact_email = models.EmailField()
    
    # Approval workflow
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                  related_name='approved_requests')
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True)
    
    # Real-time tracking fields (NEW)
    max_donors = models.IntegerField(default=5, help_text="Maximum donors that can respond")
    auto_expire_hours = models.IntegerField(default=6, help_text="Auto-expire after X hours")
    tracking_enabled = models.BooleanField(default=True, help_text="Enable live donor tracking")
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    activated_at = models.DateTimeField(null=True, blank=True, help_text="When request went live")
    
    # Phase 6: Status History Tracking (JSON field)
    status_history = models.JSONField(default=list, blank=True, help_text="Track all status changes with timestamps")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['city', 'patient_blood_group']),
            models.Index(fields=['latitude', 'longitude']),  # For location-based queries
        ]
    
    def __str__(self):
        return f"Request #{self.id} - {self.patient_blood_group} - {self.hospital_name}"
    
    def save(self, *args, **kwargs):
        # Track status changes for Phase 6
        if self.pk:  # Only for existing objects
            try:
                old_instance = BloodRequest.objects.get(pk=self.pk)
                if old_instance.status != self.status:
                    # Status changed - record it
                    status_entry = {
                        'old_status': old_instance.status,
                        'new_status': self.status,
                        'timestamp': timezone.now().isoformat(),
                        'changed_by': str(self.approved_by) if self.approved_by else 'system',
                    }
                    
                    # Initialize or append to history
                    if not self.status_history:
                        self.status_history = []
                    self.status_history.append(status_entry)
                    
                    logger.info(f"Status change tracked for request #{self.pk}: {old_instance.status} → {self.status}")
            except BloodRequest.DoesNotExist:
                pass  # New object, no history yet
        
        # Set expiration time
        if not self.expires_at:
            if self.priority == 'emergency':
                self.expires_at = self.required_by + timezone.timedelta(hours=self.auto_expire_hours or 6)
            elif self.priority == 'urgent':
                self.expires_at = self.required_by + timezone.timedelta(days=1)
            else:
                self.expires_at = self.required_by + timezone.timedelta(days=3)

        # Auto-approve emergency and urgent requests
        if self.status == 'pending' and self.priority in ['emergency', 'urgent']:
            self.status = 'approved'
            self.approved_by = self.requester if self.requester else None
            self.approved_at = timezone.now()
            self.approval_notes = 'Auto-approved due to emergency/urgent priority'
            self.activated_at = timezone.now()
            logger.info(f"Auto-approved request #{self.pk} due to {self.priority} priority")

        # Auto-approve normal requests after 5 minutes (for testing/demo)
        elif self.status == 'pending' and self.priority == 'normal':
            # Check if request is older than 5 minutes
            if self.created_at and (timezone.now() - self.created_at).total_seconds() > 300:
                self.status = 'approved'
                self.approved_by = self.requester if self.requester else None
                self.approved_at = timezone.now()
                self.approval_notes = 'Auto-approved after 5 minutes'
                self.activated_at = timezone.now()
                logger.info(f"Auto-approved normal request #{self.pk} after 5 minutes")

        # Auto-activate when approved
        if self.status == 'active' and not self.activated_at:
            self.activated_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    @property
    def is_active(self):
        return self.status in ['active', 'partially_fulfilled'] and not self.is_expired
    
    @property
    def remaining_units(self):
        return self.required_units - self.fulfilled_units
    
    @property
    def completion_percentage(self):
        if self.required_units == 0:
            return 0
        return (self.fulfilled_units / self.required_units) * 100
    
    @property
    def active_responses_count(self):
        """Count of donors who responded positively"""
        return self.responses.filter(status__in=['interested', 'en_route', 'arrived']).count()
    
    @property
    def can_accept_more_donors(self):
        """Check if request can accept more donor responses"""
        return self.active_responses_count < self.max_donors
    
    def add_status_change(self, new_status, notes="", changed_by="system"):
        """Manually add a status change entry to history"""
        if not self.status_history:
            self.status_history = []
        
        status_entry = {
            'old_status': self.status,
            'new_status': new_status,
            'timestamp': timezone.now().isoformat(),
            'changed_by': str(changed_by),
            'notes': notes,
        }
        
        self.status_history.append(status_entry)
        logger.info(f"Status change recorded for request #{self.id}: {self.status} → {new_status}")
    
    def check_and_expire(self):
        """Check if request should be expired based on time"""
        if self.status in ['fulfilled', 'cancelled', 'expired']:
            return False
        
        if timezone.now() > self.expires_at:
            old_status = self.status
            self.status = 'expired'
            self.add_status_change('expired', 'Request expired due to time limit')
            self.save(update_fields=['status', 'updated_at', 'status_history'])
            return True
        return False
    
    def check_duplicate_request(self, user, blood_group, city, hours=24):
        """Check for duplicate requests from same user within specified hours"""
        from django.utils import timezone
        cutoff_time = timezone.now() - timezone.timedelta(hours=hours)
        
        duplicates = BloodRequest.objects.filter(
            requester=user,
            patient_blood_group=blood_group,
            city=city,
            created_at__gte=cutoff_time,
            status__in=['pending', 'approved', 'active', 'partially_fulfilled']
        ).exclude(id=self.id if self.id else None)
        
        return duplicates.exists()
    
    @property
    def average_rating(self):
        """Calculate average rating for this request's donors"""
        ratings = self.donor_ratings.all()
        if ratings.exists():
            return sum(r.rating for r in ratings) / ratings.count()
        return 0
    
    def find_matching_donors(self, max_distance_km=50, limit=20):
        """Smart donor matching algorithm based on multiple factors"""
        from django.db.models import Q, F
        from accounts.models import User
        
        # Get eligible donors
        eligible_donors = User.objects.filter(
            is_donor=True,
            is_active=True,
            is_available=True,
            is_verified=True,
            blood_group=self.patient_blood_group
        ).exclude(id=self.requester.id)
        
        # Calculate distance for each donor
        matched_donors = []
        for donor in eligible_donors:
            if hasattr(donor, 'latitude') and hasattr(donor, 'longitude') and donor.latitude and donor.longitude:
                distance = self.calculate_distance(
                    float(self.latitude), float(self.longitude),
                    float(donor.latitude), float(donor.longitude)
                )
                
                if distance <= max_distance_km:
                    # Calculate compatibility score
                    score = self.calculate_compatibility_score(donor, distance)
                    matched_donors.append({
                        'donor': donor,
                        'distance': distance,
                        'score': score
                    })
        
        # Sort by compatibility score (highest first)
        matched_donors.sort(key=lambda x: x['score'], reverse=True)
        
        return matched_donors[:limit]
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points using Haversine formula"""
        import math
        R = 6371  # Earth's radius in km
        dLat = (lat2 - lat1) * math.pi / 180
        dLon = (lon2 - lon1) * math.pi / 180
        a = math.sin(dLat/2) * math.sin(dLat/2) + \
            math.cos(lat1 * math.pi / 180) * math.cos(lat2 * math.pi / 180) * \
            math.sin(dLon/2) * math.sin(dLon/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
    
    def calculate_compatibility_score(self, donor, distance):
        """Calculate compatibility score for donor matching"""
        score = 100
        
        # Distance penalty (closer is better)
        if distance <= 5:
            score += 30
        elif distance <= 10:
            score += 20
        elif distance <= 20:
            score += 10
        elif distance <= 50:
            score += 5
        
        # Trust score bonus
        score += donor.trust_score * 0.3
        
        # Donation history bonus
        score += donor.donations_completed * 2
        
        # Recent donation penalty (if donated recently, might not be eligible)
        if donor.last_donation_date:
            days_since = (timezone.now().date() - donor.last_donation_date).days
            if days_since < 90:
                score -= 50  # Not eligible yet
            elif days_since < 120:
                score -= 10  # Recently donated, lower priority
        
        # Cap score at 100
        return min(100, max(0, score))
    
    def activate_request(self):
        """Activate the request and start searching for donors"""
        if self.status == 'approved':
            self.status = 'active'
            self.activated_at = timezone.now()
            self.add_status_change('active', 'Request activated and searching for donors')
            self.save(update_fields=['status', 'activated_at', 'updated_at', 'status_history'])
            logger.info(f"Request #{self.id} activated")
            return True
        return False
    
    def mark_as_fulfilled(self):
        """Mark request as fully fulfilled"""
        if self.fulfilled_units >= self.required_units:
            old_status = self.status
            self.status = 'fulfilled'
            self.add_status_change('fulfilled', f'All {self.required_units} units fulfilled')
            self.save(update_fields=['status', 'updated_at', 'status_history'])
            logger.info(f"Request #{self.id} fulfilled: {old_status} → fulfilled")
            return True
        return False


class RequestResponse(models.Model):
    """Donor response to blood request (NEW MODEL)"""
    
    STATUS_CHOICES = [
        ('interested', 'Interested - Will Donate'),
        ('en_route', 'En Route to Hospital'),
        ('arrived', 'Arrived at Hospital'),
        ('donated', 'Donation Completed'),
        ('unavailable', 'No Longer Available'),
        ('declined', 'Declined'),
    ]
    
    request = models.ForeignKey(BloodRequest, on_delete=models.CASCADE, related_name='responses')
    donor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='request_responses')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='interested')
    
    # Response timestamps
    responded_at = models.DateTimeField(default=timezone.now)
    en_route_at = models.DateTimeField(null=True, blank=True)
    arrived_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Donor location tracking (for live map)
    donor_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    donor_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    last_location_update = models.DateTimeField(null=True, blank=True)
    
    # Distance and ETA
    distance_km = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    estimated_arrival_minutes = models.IntegerField(null=True, blank=True)
    
    # Selection by requester
    is_selected = models.BooleanField(default=False, help_text="Selected by requester")
    selected_at = models.DateTimeField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['request', 'donor']
        ordering = ['-responded_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['is_selected']),
        ]
    
    def __str__(self):
        return f"{self.donor.username} → Request #{self.request.id} ({self.status})"
    
    def update_location(self, latitude, longitude):
        """Update donor's current location"""
        self.donor_latitude = latitude
        self.donor_longitude = longitude
        self.last_location_update = timezone.now()
        self.save(update_fields=['donor_latitude', 'donor_longitude', 'last_location_update'])
    
    @property
    def response_time_minutes(self):
        """Minutes since donor responded"""
        if not self.responded_at:
            return None
        return (timezone.now() - self.responded_at).total_seconds() / 60


class DonorLocationHistory(models.Model):
    """Track donor location history for privacy and analytics (NEW MODEL)"""
    
    donor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='location_history')
    request = models.ForeignKey(BloodRequest, on_delete=models.CASCADE, related_name='location_tracking', null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    accuracy_meters = models.FloatField(null=True, blank=True, help_text="GPS accuracy in meters")
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['donor', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.donor.username} @ ({self.latitude}, {self.longitude}) - {self.timestamp}"


# Keep existing models for backward compatibility
class RequestMatch(models.Model):
    """Legacy match model - will be phased out in favor of RequestResponse"""
    
    STATUS_CHOICES = [
        ('proposed', 'Proposed to Donor'),
        ('accepted', 'Donor Accepted'),
        ('declined', 'Donor Declined'),
        ('completed', 'Donation Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    request = models.ForeignKey(BloodRequest, on_delete=models.CASCADE, related_name='matches')
    donor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='request_matches')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='proposed')
    proposed_at = models.DateTimeField(default=timezone.now)
    responded_at = models.DateTimeField(null=True, blank=True)
    donation_scheduled_at = models.DateTimeField(null=True, blank=True)
    donation_completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    # Matching details
    distance_km = models.DecimalField(max_digits=6, decimal_places=2)
    compatibility_score = models.DecimalField(max_digits=5, decimal_places=2)
    
    class Meta:
        unique_together = ['request', 'donor']
        ordering = ['-proposed_at']
    
    def __str__(self):
        return f"Match: {self.request.id} - {self.donor.username} ({self.status})"


class RequestUpdate(models.Model):
    """Track updates and status changes for requests"""
    
    request = models.ForeignKey(BloodRequest, on_delete=models.CASCADE, related_name='updates')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    status_from = models.CharField(max_length=20, choices=BloodRequest.STATUS_CHOICES)
    status_to = models.CharField(max_length=20, choices=BloodRequest.STATUS_CHOICES)
    notes = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Request {self.request.id}: {self.status_from} → {self.status_to}"


# ChatMessage moved to models_chat.py to avoid conflicts
from .models_chat import ChatMessage  # Import from separate file


# Register for audit logging
auditlog.register(BloodRequest)
auditlog.register(RequestResponse)
auditlog.register(DonorLocationHistory)
auditlog.register(RequestMatch)
auditlog.register(RequestUpdate)
auditlog.register(ChatMessage)
auditlog.register(DonorRating)