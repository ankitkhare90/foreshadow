import os

from dotenv import load_dotenv

load_dotenv()

def geo_tag_events(events):
    """Add geographic coordinates and influence radius to events"""
    tagged_events = []
    
    for index, event in enumerate(events):
        event_copy = event.copy()
        if "location" in event_copy and event_copy["location"]:
            city = event_copy.get("city_name", "")
            country_code = event_copy.get("country_code", "")
            full_location = format_full_location(event_copy["location"], city, country_code)
            print("--------------------------------")
            print(f"Full location: {full_location}")
            coordinates = fetch_lat_long(full_location, index, country_code, city)
            print(f"Coordinates: {coordinates}")
            print("--------------------------------")
            event_copy["latitude"] = coordinates[0]
            event_copy["longitude"] = coordinates[1]
            
            # Set influence radius based on traffic impact
            traffic_impact = event_copy.get("traffic_impact", "").lower()
            if traffic_impact == "high":
                event_copy["influence_radius"] = 2.5
            elif traffic_impact == "medium":
                event_copy["influence_radius"] = 1.5
            else:  # low or unknown
                event_copy["influence_radius"] = 1.0
        
        tagged_events.append(event_copy)
    
    return tagged_events

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
    address: str, 
    row_idx: Any,
    country_code, 
    city: str = "",
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
            "id": "",
            "placeName": "",
            "formattedAddress": address,
            "city": city if city else "",
            "countryCode": country_code,
            "locationType": "",
            "placeHash": ""
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