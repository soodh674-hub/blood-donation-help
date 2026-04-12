from django.db import models
from django.utils import timezone
from accounts.models import User
from auditlog.registry import auditlog
import logging

logger = logging.getLogger(__name__)

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


class ChatMessage(models.Model):
    """Real-time chat between donor and requester"""
    request = models.ForeignKey(BloodRequest, on_delete=models.CASCADE, related_name='chat_messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['request', 'timestamp']),
        ]
    
    def __str__(self):
        return f"Message from {self.sender.username} at {self.timestamp}"


class DonorRating(models.Model):
    """Rating system for donors and requesters"""
    rater = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_ratings')
    rated_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_ratings')
    request = models.ForeignKey(BloodRequest, on_delete=models.CASCADE, related_name='ratings')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 stars
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['rater', 'rated_user', 'request']
    
    @property
    def average_rating(self):
        """Get user's average rating"""
        ratings = self.__class__.objects.filter(rated_user=self.rated_user)
        return ratings.aggregate(avg=models.Avg('rating'))['avg'] or 0


# Register for audit logging
auditlog.register(BloodRequest)
auditlog.register(RequestResponse)
auditlog.register(DonorLocationHistory)
auditlog.register(RequestMatch)
auditlog.register(RequestUpdate)
auditlog.register(ChatMessage)
auditlog.register(DonorRating)