# Region mapper for HotelRAGAgent
# Provides a simple function to retrieve RegionSettings based on location (city).

from .region_settings import REGION_MAP, DEFAULT, RegionSettings

def get_region_settings(location: str) -> RegionSettings:
    """Return the RegionSettings for a given location.

    Args:
        location: City name (e.g., "Seoul", "Tokyo", "New York").
    Returns:
        RegionSettings instance. If the location is not in REGION_MAP, the default
        settings are returned.
    """
    return REGION_MAP.get(location, DEFAULT)
