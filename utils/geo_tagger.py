import os

from dotenv import load_dotenv
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from geopy.geocoders import Nominatim

load_dotenv()

# Create a single geolocator instance to be reused
_geolocator = Nominatim(user_agent="traffic_predictor")

def get_geolocator():
    """Get the shared geolocator instance"""
    return _geolocator

def geo_tag_events(events):
    """Add geographic coordinates and influence radius to events"""
    tagged_events = []
    
    for event in events:
        event_copy = event.copy()
        if "location" in event_copy and event_copy["location"]:
            # Create full location using city_name and country_code
            city = event_copy.get("city_name", "")
            country_code = event_copy.get("country_code", "")
            full_location = format_full_location(event_copy["location"], city, country_code)
            
            coordinates = geocode_location(full_location)
            event_copy["coordinates"] = coordinates
            
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

def format_full_location(location, city="", country_code=""):
    """Format a complete location string using location, city and country code"""
    parts = [p for p in [location, city, country_code] if p]
    return ", ".join(parts)

def geocode_location(location):
    """Convert a location string to geographic coordinates"""
    geolocator = get_geolocator()
    
    try:
        location_data = geolocator.geocode(location)
        if location_data:
            return (location_data.latitude, location_data.longitude)
    except (GeocoderTimedOut, GeocoderUnavailable) as e:
        print(f"Geocoding error for: {location}, {e}")
    
    return None 