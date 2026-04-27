"""
Utility functions for blood request system
"""
from math import radians, sin, cos, sqrt, atan2


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two coordinates using Haversine formula
    
    Args:
        lat1, lon1: Coordinates of point 1
        lat2, lon2: Coordinates of point 2
    
    Returns:
        Distance in kilometers
    """
    R = 6371  # Earth's radius in km
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c
