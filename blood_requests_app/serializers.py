from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta

from accounts.serializers import UserPublicSerializer
from .models import BloodRequest, RequestMatch, DonorRating
from .models_chat import ChatMessage
from donors.models import DonorAvailability


class ChatMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)
    
    class Meta:
        model = ChatMessage
        fields = ['id', 'sender', 'sender_name', 'message', 'timestamp', 'is_read']


class DonorRatingSerializer(serializers.ModelSerializer):
    rater_name = serializers.CharField(source='rater.get_full_name', read_only=True)
    
    class Meta:
        model = DonorRating
        fields = '__all__'


class DonorAvailabilitySerializer(serializers.ModelSerializer):
    donor_name = serializers.CharField(source='donor.get_full_name', read_only=True)
    distance_km = serializers.SerializerMethodField()
    
    class Meta:
        model = DonorAvailability
        fields = '__all__'
    
    def get_distance_km(self, obj):
        if obj.current_latitude and obj.current_longitude:
            # Calculate distance from request location
            request_id = self.context.get('request_id')
            if request_id:
                try:
                    from math import radians, cos, sin, sqrt, atan2
                    request = BloodRequest.objects.get(id=request_id)
                    
                    lat1, lon1 = float(obj.current_latitude), float(obj.current_longitude)
                    lat2, lon2 = float(request.latitude), float(request.longitude)
                    
                    R = 6371  # Earth radius in km
                    dlat = radians(lat2 - lat1)
                    dlon = radians(lon2 - lon1)
                    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
                    c = 2 * atan2(sqrt(a), sqrt(1-a))
                    return round(R * c, 2)
                except Exception:
                    return None
        return None


class BloodRequestSerializer(serializers.ModelSerializer):
    requester = UserPublicSerializer(read_only=True)

    remaining_units = serializers.ReadOnlyField()
    completion_percentage = serializers.ReadOnlyField()

    class Meta:
        model = BloodRequest
        fields = [
            "id",
            "requester",
            "patient_name",
            "patient_age",
            "patient_blood_group",
            "required_units",
            "fulfilled_units",
            "remaining_units",
            "completion_percentage",
            "priority",
            "status",
            "requester_type",
            "reason",
            "required_by",
            "medical_certificate",
            "is_critical",
            "hospital_name",
            "city",
            "state",
            "country",
            "latitude",
            "longitude",
            "contact_person",
            "contact_phone",
            "contact_email",
            "approved_by",
            "approved_at",
            "approval_notes",
            "created_at",
            "updated_at",
            "expires_at",
        ]
        read_only_fields = [
            "id",
            "requester",
            "fulfilled_units",
            "remaining_units",
            "completion_percentage",
            "approved_by",
            "approved_at",
            "created_at",
            "updated_at",
            "expires_at",
        ]


class BloodRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BloodRequest
        fields = [
            "patient_name",
            "patient_age",
            "patient_blood_group",
            "required_units",
            "priority",
            "requester_type",
            "reason",
            "required_by",
            "medical_certificate",
            "is_critical",
            "hospital_name",
            "city",
            "state",
            "country",
            "latitude",
            "longitude",
            "contact_person",
            "contact_phone",
            "contact_email",
            "pincode",
        ]
    
    def validate_patient_age(self, value):
        if value <= 0 or value > 150:
            raise serializers.ValidationError("Patient age must be between 1 and 150.")
        return value
    
    def validate_required_units(self, value):
        if value <= 0 or value > 10:
            raise serializers.ValidationError("Required units must be between 1 and 10.")
        return value
    
    def validate_pincode(self, value):
        if value and str(value).strip() != '' and len(str(value)) != 6:
            raise serializers.ValidationError("Pincode must be exactly 6 digits.")
        return value if value else None  # Return None if empty to handle optional field properly
    
    def validate_contact_phone(self, value):
        if value and len(str(value)) < 10:
            raise serializers.ValidationError("Phone number must be at least 10 digits.")
        return value

    def create(self, validated_data):
        """Override create to properly set expires_at based on priority"""
        from django.utils import timezone
        from datetime import timedelta

        # Get priority
        priority = validated_data.get('priority', 'normal')
        required_by = validated_data.get('required_by')

        # Set expires_at based on priority
        now = timezone.now()
        if priority == 'emergency':
            # Emergency requests expire in 6 hours
            validated_data['expires_at'] = now + timedelta(hours=6)
        elif priority == 'urgent':
            # Urgent requests expire in 24 hours
            validated_data['expires_at'] = now + timedelta(hours=24)
        else:
            # Normal requests expire in 72 hours (3 days)
            validated_data['expires_at'] = now + timedelta(hours=72)

        # If required_by is not provided or is in the past, set it to expires_at
        if not required_by or required_by < now:
            validated_data['required_by'] = validated_data['expires_at']

        # Create the request
        blood_request = BloodRequest.objects.create(**validated_data)
        return blood_request


class RequestMatchDonorSerializer(UserPublicSerializer):
    class Meta(UserPublicSerializer.Meta):
        fields = UserPublicSerializer.Meta.fields + ["blood_group"]


class RequestMatchSerializer(serializers.ModelSerializer):
    donor = RequestMatchDonorSerializer(read_only=True)

    class Meta:
        model = RequestMatch
        fields = [
            "id",
            "donor",
            "status",
            "proposed_at",
            "responded_at",
            "donation_scheduled_at",
            "donation_completed_at",
            "notes",
            "distance_km",
            "compatibility_score",
        ]


class BloodRequestDetailSerializer(BloodRequestSerializer):
    matches = RequestMatchSerializer(many=True, read_only=True)

    class Meta(BloodRequestSerializer.Meta):
        fields = BloodRequestSerializer.Meta.fields + ["matches"]


