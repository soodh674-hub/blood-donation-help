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
                donors = User.objects.filter(
                    blood_group=blood_group,
                    is_available=True,
                    is_active=True
                )
                
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
            matches = BloodMatcher.get_best_matching_donors(
                blood_group=blood_group,
                latitude=latitude,
                longitude=longitude,
                priority=priority,
                limit=100,  # Increase limit to accommodate filtering
            )

            # Apply additional filters
            filtered_matches = []
            for match in matches:
                donor = match["donor"]
                
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


@login_required
def donor_profile(request, user_id):
    """
    Display donor profile page (Instagram-style)
    """
    try:
        donor = get_object_or_404(User, id=user_id, user_type='donor', is_active=True)
        
        # Get donation history stats
        total_donations = DonorHistory.objects.filter(donor=donor).count()
        
        # Calculate days since last donation
        last_donation = DonorHistory.objects.filter(donor=donor).order_by('-donation_date').first()
        if last_donation:
            days_since_last = (timezone.now().date() - last_donation.donation_date.date()).days
        else:
            days_since_last = None
        
        # Count compatible recipients (how many blood groups this donor can donate to)
        compatibility_count = len(BloodMatcher.get_compatibility_info(donor.blood_group)['can_donate_to'])
        
        context = {
            'donor': donor,
            'total_donations': total_donations,
            'days_since_last': days_since_last,
            'compatibility_count': compatibility_count,
        }
        
        return render(request, 'donors/donor_profile.html', context)
    except Exception as e:
        logger.error(f'Error loading donor profile: {str(e)}', exc_info=True)
        return render(request, 'donors/donor_profile.html', {'error': 'Profile not found'})


