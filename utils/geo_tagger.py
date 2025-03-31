import os
from math import radians, cos, sin, asin, sqrt

from dotenv import load_dotenv

load_dotenv()

def geo_tag_events(events, city, country_code, max_distance_km=100):
    """Add geographic coordinates as latitude and longitude to events
    
    Args:
        events: List of event dictionaries
        city: City name for coordinates reference
        country_code: Two-letter country code
        max_distance_km: Maximum distance in kilometers from city center (default: 100)
    
    Returns:
        List of events with geographic coordinates, filtered by distance
    """
    tagged_events = []
    
    city_coordinates = fetch_lat_long(1, f"{city}, {country_code}", city, country_code)
    
    for index, event in enumerate(events):
        event_copy = event.copy()
        if "location" in event_copy and event_copy["location"]:
            city = event_copy.get("city_name", "")
            country_code = event_copy.get("country_code", "")
            full_location = format_full_location(event_copy["location"], city, country_code)
            coordinates = fetch_lat_long(row_idx=index, address=full_location, 
                                         city=city, country_code=country_code)

            event_copy["latitude"] = coordinates[0]
            event_copy["longitude"] = coordinates[1]
            
            # Skip events with invalid coordinates
            if not coordinates[0] or not coordinates[1]:
                continue
                
            # Skip events that are too far from the city center
            if city_coordinates[0] and city_coordinates[1]:
                distance = haversine_distance(
                    city_coordinates[0], city_coordinates[1],
                    coordinates[0], coordinates[1]
                )
                
                event_copy["distance_from_city_km"] = distance
                
                if distance > max_distance_km:
                    continue
                    
            # Only include events with valid location information
            tagged_events.append(event_copy)
    
    return tagged_events

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    
    Returns:
        Distance in kilometers
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r

def format_full_location(location, city, country_code):
    """Format a complete location string using location, city and country code"""
    parts = [p for p in [location, city, country_code] if p]
    return ", ".join(parts)


"""
Geocoding utilities for converting addresses to coordinates.
"""

import json
import os
from typing import Any, Callable, Optional, Tuple

import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

from config.constants import GEOCODE_API_URL

load_dotenv()

user_id = os.getenv("GEOCODE_USERNAME")
password = os.getenv("GEOCODE_PWD")

def fetch_lat_long(
    row_idx: Any,
    address: str, 
    city: str,
    country_code: str,
    error_callback: Optional[Callable] = None
) -> Tuple[Optional[float], Optional[float]]:
    """
    Fetch latitude and longitude for a given address using the geocoding API.
    
    Args:
        address: The address to geocode
        row_idx: Unique identifier for the row (used as request ID)
        user_id: API user ID for authentication (with mara/personnel prefix)
        password: API password for authentication
        country_code: Two-letter country code (default: "in")
        city: City name (optional)
        error_callback: Optional callback function for error handling
        
    Returns:
        Tuple of (latitude, longitude) or (None, None) if geocoding failed
    """
    # Use row index as the unique ID
    unique_id = f"row-{row_idx}"
    
    payload = {
        "id": unique_id,
        "address": {
            "formattedAddress": address,
            "city": city,
            "countryCode": country_code
        }
    }
    
    try:
        response = requests.post(
            GEOCODE_API_URL, 
            auth=HTTPBasicAuth(user_id, password), 
            headers={"Content-Type": "application/json"}, 
            data=json.dumps(payload),
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if "latLng" in result and "lat" in result["latLng"] and "lng" in result["latLng"]:
                return result["latLng"]["lat"], result["latLng"]["lng"]
        else:
            if error_callback:
                error_callback(f"API Error {response.status_code}: {response.text}")
    except Exception as e:
        if error_callback:
            error_callback(f"Request failed: {str(e)}")
    
    return None, None