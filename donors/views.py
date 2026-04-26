from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
import logging

from accounts.models import User
from accounts.serializers import UserPublicSerializer
from donors.models import DonorHistory
from .matching import BloodMatcher

# Setup logging
logger = logging.getLogger(__name__)


class DonorSearchView(generics.ListAPIView):
    """
    Search for best-matching donors using the BloodMatcher.

    Query params:
    - blood_group (required)
    - latitude (required for authenticated users)
    - longitude (required for authenticated users)
    - max_distance (optional, default 25)
    - priority (optional: normal|urgent|emergency, default normal)
    - pincode (optional)
    - city (optional)
    """

    permission_classes = [AllowAny]  # Allow public access
    serializer_class = UserPublicSerializer

    def list(self, request, *args, **kwargs):
        try:
            blood_group = request.query_params.get("blood_group")
            latitude = request.query_params.get("latitude")
            longitude = request.query_params.get("longitude")
            max_distance = request.query_params.get("max_distance", 25)
            priority = request.query_params.get("priority", "normal")
            pincode = request.query_params.get("pincode")
            city = request.query_params.get("city")

            if not blood_group:
                logger.warning(f'Missing required parameter: blood_group={blood_group}')
                return Response(
                    {
                        "detail": "blood_group is required."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # For searches with only blood group (no location), return all donors with that blood group
            if not latitude or not longitude:
                # Return all available donors with matching blood group regardless of location
                # Optimized with select_related and prefetch_related to reduce database queries
                try:
                    donors = User.objects.filter(
                        user_type='donor',
                        blood_group=blood_group,
                        is_available=True,
                        is_active=True
                    ).select_related('donor_profile')
                except Exception as e:
                    logger.error(f'Error querying donors: {str(e)}')
                    donors = User.objects.none()
                
                # EXCLUDE donors with anonymous_mode enabled
                try:
                    from accounts.models import PrivacySettings
                    anonymous_user_ids = PrivacySettings.objects.filter(
                        anonymous_mode=True
                    ).values_list('user_id', flat=True)
                    donors = donors.exclude(id__in=anonymous_user_ids)
                except Exception as e:
                    logger.warning(f'Could not filter anonymous donors: {str(e)}')
                
                # Apply additional filters
                if pincode:
                    donors = donors.filter(pincode=pincode)
                if city:
                    donors = donors.filter(city__icontains=city)
                
                # Serialize results
                serializer = self.serializer_class(donors, many=True, context={"request": request})
                
                # Add mock distance for consistency
                results = []
                for donor_data in serializer.data:
                    donor_data['distance_km'] = None  # No distance for public searches
                    results.append({
                        "donor": donor_data,
                        "score": 100,  # Default score for public searches
                        "details": {"note": "Public search results - login for location-based matching"}
                    })
                
                logger.info(f'Public donor search completed: {len(results)} results for blood group {blood_group}')
                return Response({"count": len(results), "results": results})

            try:
                latitude = float(latitude)
                longitude = float(longitude)
                max_distance = float(max_distance)
            except (TypeError, ValueError):
                logger.warning(f'Invalid numeric parameters: latitude={latitude}, longitude={longitude}, max_distance={max_distance}')
                return Response(
                    {"detail": "latitude, longitude and max_distance must be numbers."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get matches from BloodMatcher
            try:
                matches = BloodMatcher.get_best_matching_donors(
                    blood_group=blood_group,
                    latitude=latitude,
                    longitude=longitude,
                    priority=priority,
                    limit=100,  # Increase limit to accommodate filtering
                )
            except Exception as e:
                logger.error(f'Error in BloodMatcher: {str(e)}', exc_info=True)
                # Fall back to simple search without location matching
                donors = User.objects.filter(
                    user_type='donor',
                    blood_group=blood_group,
                    is_available=True,
                    is_active=True
                ).select_related('donor_profile')
                matches = [{"donor": donor, "score": 100, "details": {"note": "Location matching unavailable"}} for donor in donors[:50]]

            # Apply additional filters
            filtered_matches = []
            for match in matches:
                donor = match["donor"]
                
                # EXCLUDE donors with anonymous_mode enabled
                try:
                    from accounts.models import PrivacySettings
                    if PrivacySettings.objects.filter(
                        user=donor, anonymous_mode=True
                    ).exists():
                        continue
                except Exception as e:
                    logger.warning(f'Could not check anonymous status for donor {donor.id}: {str(e)}')
                
                # Filter by pincode if provided
                if pincode and donor.pincode != pincode:
                    continue
                    
                # Filter by city if provided
                if city and city.lower() not in donor.city.lower():
                    continue
                    
                donor_data = UserPublicSerializer(donor, context={"request": request}).data
                filtered_matches.append(
                    {
                        "donor": donor_data,
                        "score": match["score"],
                        "details": match["details"],
                    }
                )

            # Limit results to 50
            results = filtered_matches[:50]

            logger.info(f'Donor search completed: {len(results)} results for blood group {blood_group}')
            return Response({"count": len(results), "results": results})
            
        except Exception as e:
            logger.error(f'Error in donor search: {str(e)}', exc_info=True)
            return Response(
                {"detail": "An error occurred while searching for donors."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def compatibility_info(request, blood_group):
    """
    Return compatibility information for a given blood group.
    """
    try:
        info = BloodMatcher.get_compatibility_info(blood_group)
        logger.info(f'Compatibility info requested for blood group: {blood_group}')
        return Response(info)
    except Exception as e:
        logger.error(f'Error getting compatibility info for {blood_group}: {str(e)}', exc_info=True)
        return Response(
            {"detail": "An error occurred while fetching compatibility information."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from django.core.cache import cache


@cache_page(60 * 5)  # Cache for 5 minutes
def donor_profile(request, user_id):
    """
    Display donor profile page (Instagram-style)
    Phase 3: Added caching for performance optimization
    Public view - no login required to view donor profiles
    """
    try:
        # Try to get cached profile data
        cache_key = f'donor_profile_{user_id}'
        cached_data = cache.get(cache_key)

        if cached_data:
            donor = User.objects.get(id=user_id)
            context = {
                'donor': donor,
                **cached_data
            }
            return render(request, 'donors/donor_profile.html', context)

        donor = get_object_or_404(
            User.objects.select_related('donor_profile'),
            id=user_id, user_type='donor', is_active=True
        )

        # Get donation history stats - optimized with count()
        total_donations = DonorHistory.objects.filter(donor=donor).count()

        # Get donation history for timeline - optimized with only()
        donation_history = DonorHistory.objects.filter(donor=donor).order_by('-donation_date').only(
            'donation_date', 'location', 'notes'
        )[:10]

        # Calculate days since last donation
        last_donation = DonorHistory.objects.filter(donor=donor).order_by('-donation_date').first()
        if last_donation:
            days_since_last = (timezone.now().date() - last_donation.donation_date.date()).days
        else:
            days_since_last = None

        # Count compatible recipients (how many blood groups this donor can donate to)
        compatibility_info = BloodMatcher.get_compatibility_info(donor.blood_group)
        compatibility_count = compatibility_info.get('total_compatible_types', 0)

        # Get total requests completed
        total_requests = BloodRequest.objects.filter(donor=donor, status='fulfilled').count()

        # Calculate rating (placeholder - can be enhanced later)
        rating = getattr(donor.donor_profile, 'rating', 0) if hasattr(donor, 'donor_profile') and donor.donor_profile else 0

        context_data = {
            'total_donations': total_donations,
            'donation_history': donation_history,
            'days_since_last': days_since_last,
            'compatibility_count': compatibility_count,
            'total_requests': total_requests,
            'rating': rating,
        }

        # Cache the computed data (not the donor object)
        cache.set(cache_key, context_data, 60 * 5)  # 5 minutes

        context = {
            'donor': donor,
            **context_data
        }

        return render(request, 'donors/donor_profile.html', context)
    except Exception as e:
        logger.error(f'Error loading donor profile: {str(e)}', exc_info=True)
        return render(request, 'donors/donor_profile.html', {'error': 'Profile not found'})


@login_required
def recommended_donors(request):
    """
    Phase 3: Recommend compatible donors based on blood group and location
    Uses a simple recommendation algorithm considering:
    - Blood group compatibility
    - Geographic proximity
    - Donation availability
    - Recent activity
    """
    try:
        if not request.user.blood_group:
            return render(request, 'donors/recommended.html', {
                'error': 'Please set your blood group in your profile to get recommendations'
            })

        # Get compatible blood groups
        compatibility_info = BloodMatcher.get_compatibility_info(request.user.blood_group)
        compatible_blood_groups = compatibility_info.get('compatible_donors', [])

        # Get user's location if available
        user_lat = getattr(request.user, 'latitude', None)
        user_lng = getattr(request.user, 'longitude', None)

        # Base queryset: active donors with compatible blood groups
        # Optimized with select_related and only() to reduce database queries
        recommended_donors = User.objects.filter(
            user_type='donor',
            is_active=True,
            is_available=True,
            blood_group__in=compatible_blood_groups
        ).exclude(id=request.user.id).select_related('donor_profile')

        # Calculate recommendation scores
        scored_donors = []
        for donor in recommended_donors:
            score = 0

            # Base score for being compatible
            score += 50

            # Bonus for verified donors
            if donor.is_verified:
                score += 20

            # Bonus for recent donations (active donors)
            if donor.last_donation_date:
                days_since = (timezone.now().date() - donor.last_donation_date).days
                if days_since < 90:  # Donated in last 3 months
                    score += 15
                elif days_since < 180:  # Donated in last 6 months
                    score += 10

            # Bonus for proximity if location available
            if user_lat and user_lng and hasattr(donor, 'latitude') and hasattr(donor, 'longitude'):
                distance = calculate_distance(
                    float(user_lat), float(user_lng),
                    float(donor.latitude), float(donor.longitude)
                )
                if distance < 10:  # Within 10km
                    score += 30
                elif distance < 50:  # Within 50km
                    score += 20
                elif distance < 100:  # Within 100km
                    score += 10

            # Bonus for total donations (experienced donors)
            total_donations = DonorHistory.objects.filter(donor=donor).count()
            if total_donations >= 10:
                score += 15
            elif total_donations >= 5:
                score += 10
            elif total_donations >= 1:
                score += 5

            scored_donors.append({
                'donor': donor,
                'score': score,
                'distance': calculate_distance(user_lat, user_lng, donor.latitude, donor.longitude) if user_lat and user_lng and hasattr(donor, 'latitude') else None
            })

        # Sort by score (highest first)
        scored_donors.sort(key=lambda x: x['score'], reverse=True)

        # Get top 10 recommendations
        top_recommendations = scored_donors[:10]

        return render(request, 'donors/recommended.html', {
            'recommended_donors': top_recommendations,
            'compatible_blood_groups': compatible_blood_groups
        })

    except Exception as e:
        logger.error(f'Error getting recommended donors: {str(e)}', exc_info=True)
        return render(request, 'donors/recommended.html', {'error': 'Failed to load recommendations'})


def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates using Haversine formula"""
    from math import radians, cos, sin, sqrt, atan2

    R = 6371  # Earth radius in km

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))

    return R * c


