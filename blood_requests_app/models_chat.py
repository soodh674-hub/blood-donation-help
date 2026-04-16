from django.db import models
from django.utils import timezone
from accounts.models import User

class ChatMessage(models.Model):
    """Model for real-time chat messages between users"""

    MESSAGE_TYPES = [
        ('text', 'Text Message'),
        ('system', 'System Message'),
        ('emergency', 'Emergency Alert'),
    ]

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    message = models.TextField()
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    is_read = models.BooleanField(default=False)
    # Optional link to blood request (nullable to avoid migration issues)
    request = models.ForeignKey('BloodRequest', on_delete=models.CASCADE, null=True, blank=True, related_name='chat_messages')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sender', 'receiver', 'created_at']),
            models.Index(fields=['receiver', 'is_read', 'created_at']),
        ]
    
    def __str__(self):
        return f"From {self.sender.username} to {self.receiver.username}: {self.message[:50]}..."

class ChatRoom(models.Model):
    """Model for chat rooms (group conversations)"""
    
    ROOM_TYPES = [
        ('request', 'Request-specific Room'),
        ('emergency', 'Emergency Alert Room'),
        ('general', 'General Discussion'),
    ]
    
    name = models.CharField(max_length=100)
    room_type = models.CharField(max_length=10, choices=ROOM_TYPES, default='request')
    blood_request = models.ForeignKey('BloodRequest', on_delete=models.CASCADE, null=True, blank=True)
    participants = models.ManyToManyField(User, related_name='chat_rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_room_type_display()})"

class RoomMessage(models.Model):
    """Model for messages in chat rooms"""
    
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['room', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.sender.username} in {self.room.name}: {self.message[:50]}..."

class NotificationMessage(models.Model):
    """Model for system notifications"""
    
    NOTIFICATION_TYPES = [
        ('new_request', 'New Blood Request'),
        ('donor_response', 'Donor Response'),
        ('request_fulfilled', 'Request Fulfilled'),
        ('emergency_alert', 'Emergency Alert'),
        ('chat_message', 'New Chat Message'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
        ('emergency', 'Emergency'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    title = models.CharField(max_length=200)
    message = models.TextField()
    related_request = models.ForeignKey('BloodRequest', on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at']),
            models.Index(fields=['user', 'priority', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username}: {self.title}"

class UserLocation(models.Model):
    """Model for tracking user locations in real-time"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='locations')
    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)
    accuracy = models.FloatField(null=True, blank=True)  # GPS accuracy in meters
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} at {self.latitude}, {self.longitude}"

class TypingIndicator(models.Model):
    """Model for tracking typing indicators in chat"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, null=True, blank=True)
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='typing_indicators')
    is_typing = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['room', 'user', 'last_updated']),
            models.Index(fields=['receiver', 'user', 'last_updated']),
        ]
    
    def __str__(self):
        return f"{self.user.username} is typing: {self.is_typing}"


class ChatbotConversation(models.Model):
    """Model for storing chatbot conversations and feedback"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='chatbot_conversations')
    session_id = models.CharField(max_length=100, unique=True)
    user_message = models.TextField()
    bot_response = models.TextField()
    confidence = models.CharField(max_length=10, default='medium')
    suggestions = models.JSONField(default=list, blank=True)
    user_context = models.JSONField(default=dict, blank=True)
    is_helpful = models.BooleanField(null=True, blank=True)  # User feedback
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session_id', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        user_str = self.user.username if self.user else 'Anonymous'
        return f"{user_str}: {self.user_message[:50]}..."
