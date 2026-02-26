"""
Distance calculation utilities using Haversine formula
"""
import math
from typing import Tuple, List


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth
    using the Haversine formula.

    Args:
        lat1: Latitude of point 1 in degrees
        lon1: Longitude of point 1 in degrees
        lat2: Latitude of point 2 in degrees
        lon2: Longitude of point 2 in degrees

    Returns:
        Distance in kilometers

    Example:
        >>> calculate_distance(40.7128, -74.0060, 34.0522, -118.2437)
        3935.746
    """
    # Earth's radius in kilometers
    R = 6371.0

    # Convert degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return round(distance, 2)


def calculate_distance_matrix(
    origin: Tuple[float, float],
    destinations: List[Tuple[float, float]]
) -> List[float]:
    """
    Calculate distances from one origin to multiple destinations.

    Args:
        origin: Tuple of (latitude, longitude) for the origin point
        destinations: List of (latitude, longitude) tuples for destinations

    Returns:
        List of distances in kilometers

    Example:
        >>> origin = (40.7128, -74.0060)
        >>> destinations = [(34.0522, -118.2437), (41.8781, -87.6298)]
        >>> calculate_distance_matrix(origin, destinations)
        [3935.75, 1145.21]
    """
    origin_lat, origin_lon = origin
    distances = []

    for dest_lat, dest_lon in destinations:
        distance = calculate_distance(origin_lat, origin_lon, dest_lat, dest_lon)
        distances.append(distance)

    return distances


def is_within_radius(
    lat1: float, lon1: float,
    lat2: float, lon2: float,
    radius_km: float
) -> bool:
    """
    Check if a point is within a given radius from another point.

    Args:
        lat1: Latitude of point 1 in degrees
        lon1: Longitude of point 1 in degrees
        lat2: Latitude of point 2 in degrees
        lon2: Longitude of point 2 in degrees
        radius_km: Radius in kilometers

    Returns:
        True if point 2 is within radius from point 1

    Example:
        >>> is_within_radius(40.7128, -74.0060, 40.7580, -73.9855, 10)
        True
    """
    distance = calculate_distance(lat1, lon1, lat2, lon2)
    return distance <= radius_km
