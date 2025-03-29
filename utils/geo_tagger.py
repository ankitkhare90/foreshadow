import openai
import os
import json
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from dotenv import load_dotenv

load_dotenv()

# Create a single geolocator instance to be reused
_geolocator = Nominatim(user_agent="traffic_predictor")

def get_openai_client():
    """Get OpenAI client with API key from environment variables"""
    api_key = os.getenv("OPENAI_API_KEY")
    return openai.OpenAI(api_key=api_key)

def get_geolocator():
    """Get the shared geolocator instance"""
    return _geolocator

def geo_tag_events(events, city="San Francisco"):
    """Add geographic coordinates and influence radius to events"""
    client = get_openai_client()
    tagged_events = []
    
    for event in events:
        event_copy = event.copy()
        if "location" in event_copy and event_copy["location"]:
            # Use LLM to disambiguate location if needed
            full_location = disambiguate_location(event_copy["location"], city, client)
            coordinates = geocode_location(full_location)
            event_copy["coordinates"] = coordinates
            
            # Calculate influence zone based on event type
            event_copy["influence_radius"] = calculate_influence_radius(event_copy, client)
        
        tagged_events.append(event_copy)
    
    return tagged_events

def disambiguate_location(location, city, client=None):
    """Disambiguate location references to include city context if needed"""
    if client is None:
        client = get_openai_client()
        
    if city.lower() in location.lower():
        return location
        
    prompt = f"""
    Disambiguate this location reference: "{location}" within the city of {city}.
    Return only the full, specific location that would be recognized by a mapping service.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=100
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error in location disambiguation: {e}")
        return f"{location}, {city}"

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

def calculate_influence_radius(event, client=None):
    """Calculate the traffic influence radius in kilometers for an event"""
    if client is None:
        client = get_openai_client()
    
    # Default radius based on event type
    default_radii = {
        "concert": 2.0,
        "festival": 3.0,
        "road closure": 1.0,
        "construction": 1.5,
        "marathon": 4.0,
        "protest": 2.5,
        "accident": 1.2
    }
    
    event_type = event.get("event_type", "").lower()
    
    # Try to get default radius
    for key, radius in default_radii.items():
        if key in event_type:
            return radius
    
    # Use LLM to determine appropriate influence radius for unknown event types
    try:
        event_json = json.dumps(event)
        prompt = f"""
        Given this event: {event_json}
        Estimate its traffic influence radius in kilometers (0.5-5).
        Return only a number.
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=10
        )
        
        radius = float(response.choices[0].message.content.strip())
        return min(max(radius, 0.5), 5)  # Clamp between 0.5 and 5 km
    except Exception as e:
        print(f"Error calculating influence radius: {e}")
        return 1.0  # Default radius 