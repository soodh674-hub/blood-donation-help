from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    
    password = serializers.CharField(write_only=True, validators=[validate_password])
    days_since_last_donation = serializers.ReadOnlyField()
    is_eligible_donor = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'user_type', 'phone_number', 'blood_group', 'date_of_birth',
            'last_donation_date', 'days_since_last_donation', 'is_eligible_donor',
            'is_verified', 'is_available', 'privacy_level',
            'city', 'state', 'country', 'pincode', 'latitude', 'longitude',
            'has_medical_conditions', 'medical_conditions', 'last_medical_checkup',
            'consent_given', 'data_retention_consent', 'password'
        ]
        read_only_fields = ['id', 'is_verified', 'created_at', 'updated_at']
    
    def validate_has_medical_conditions(self, value):
        # Handle string "true"/"false" values from form
        if isinstance(value, str):
            return value.lower() == 'true'
        return bool(value)
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile"""
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone_number', 'blood_group',
            'date_of_birth', 'is_available', 'privacy_level',
            'city', 'state', 'country', 'pincode', 'latitude', 'longitude',
            'has_medical_conditions', 'medical_conditions', 'last_medical_checkup'
        ]

class UserPublicSerializer(serializers.ModelSerializer):
    """Public serializer for user data (privacy-controlled)"""

    # Add distance field (will be added dynamically)
    distance_km = serializers.SerializerMethodField()

    # Add profile photo
    profile_photo = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name',
            'user_type', 'blood_group', 'city', 'state', 'pincode',
            'phone_number', 'distance_km', 'profile_photo'
        ]

    def get_distance_km(self, obj):
        # Return distance if available, otherwise None
        return getattr(obj, 'distance_km', None)

    def get_profile_photo(self, obj):
        # Return profile photo URL if available
        if hasattr(obj, 'donor_profile') and obj.donor_profile.profile_photo:
            return obj.donor_profile.profile_photo.url
        return None

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT token serializer"""
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims
        token['user_id'] = user.id
        token['username'] = user.username
        token['user_type'] = user.user_type
        token['is_verified'] = user.is_verified
        token['blood_group'] = user.blood_group
        
        return token

class EmailVerificationSerializer(serializers.Serializer):
    """Serializer for email verification"""
    email = serializers.EmailField()
    verification_code = serializers.CharField(max_length=6)

class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request (email only)"""
    email = serializers.EmailField()
    
    def validate_email(self, value):
        """Validate that email exists in the system"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            user = User.objects.get(email=value)
            if not user.is_active:
                raise serializers.ValidationError("Account is inactive. Please contact support.")
            return value
        except User.DoesNotExist:
            # For security, we don't reveal if email exists
            # But we'll handle this in the view
            return value

class OTPVerificationSerializer(serializers.Serializer):
    """Serializer for OTP verification"""
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6, min_length=6)
    
    def validate_otp(self, value):
        """Validate OTP format"""
        if not value.isdigit():
            raise serializers.ValidationError("OTP must contain only digits")
        return value

class PasswordResetSerializer(serializers.Serializer):
    """Serializer for password reset"""
    email = serializers.EmailField()
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    
    def validate_email(self, value):
        """Validate that email exists and has verified OTP (cache or DB)"""
        from django.contrib.auth import get_user_model
        from .models import PasswordResetOTP
        from . import services as otp_services
        User = get_user_model()
        
        try:
            user = User.objects.get(email=value)
            # Check cache first (Redis), then DB
            verified_in_cache = otp_services.is_otp_verified(user.id)
            otp_record = PasswordResetOTP.objects.filter(
                user=user,
                is_verified=True
            ).order_by('-created_at').first()
            
            if not verified_in_cache and (not otp_record or otp_record.is_expired):
                raise serializers.ValidationError("No verified OTP found. Please request a new OTP.")
            
            # Store user in context for later use
            self.context['user'] = user
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email address.")

