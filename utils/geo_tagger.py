import os
from math import asin, cos, radians, sin, sqrt
from typing import Optional, Tuple
from concurrent.futures import ThreadPoolExecutor

import googlemaps
import streamlit as st

gmaps = googlemaps.Client(key=st.secrets["GEOCODE_API"])

def geo_tag_events(events, city, country_code, 
                   max_distance_km=100, max_workers=4):
    """Add geographic coordinates as latitude and longitude to events
    
    Args:
        events: List of event dictionaries
        city: City name for coordinates reference
        country_code: Two-letter country code
        max_distance_km: Maximum distance in kilometers from city center (default: 100)
        max_workers: Maximum number of parallel workers (default: 4)
    
    Returns:
        List of events with geographic coordinates, filtered by distance
    """
    tagged_events = []
    
    city_coordinates = fetch_lat_long(f"{city}, {country_code}")
    
    def process_event(event):
        event_copy = event.copy()
        if "location" in event_copy and event_copy["location"]:
            city = event_copy.get("city_name", "")
            country_code = event_copy.get("country_code", "")
            full_location = format_full_location(event_copy["location"], city, country_code)
            coordinates = fetch_lat_long(full_location)

            event_copy["latitude"] = coordinates[0]
            event_copy["longitude"] = coordinates[1]
            
            # Skip events with invalid coordinates
            if not coordinates[0] or not coordinates[1]:
                return None
                
            # Skip events that are too far from the city center
            if city_coordinates[0] and city_coordinates[1]:
                distance = haversine_distance(
                    city_coordinates[0], city_coordinates[1],
                    coordinates[0], coordinates[1]
                )
                
                event_copy["distance_from_city_km"] = distance
                
                if distance > max_distance_km:
                    return None
                    
            # Event passes all filters
            return event_copy
        return None
    
    # Process events in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(process_event, events))
    
    # Filter out None results
    tagged_events = [event for event in results if event is not None]
    
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


def fetch_lat_long(
    address: str
) -> Tuple[Optional[float], Optional[float]]:
    """
    Fetch latitude and longitude for a given address using Google Maps geocoding API.
    
    Args:
        address: The address to geocode
        
    Returns:
        Tuple of (latitude, longitude) or (None, None) if geocoding failed
    """
    try:
        # Geocode the address
        geocode_result = gmaps.geocode(address)
        
        # Extract latitude and longitude
        if geocode_result:
            location = geocode_result[0]['geometry']['location']
            return location['lat'], location['lng']
            
    except Exception as e:
        print(f"Geocoding failed: {str(e)}")
    
    return None, None