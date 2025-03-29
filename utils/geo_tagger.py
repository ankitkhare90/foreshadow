import openai
import os
import json
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from dotenv import load_dotenv

load_dotenv()

class GeoTagger:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="traffic_predictor")
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = openai.OpenAI(api_key=self.api_key)
    
    def geo_tag_events(self, events, city="San Francisco"):
        tagged_events = []
        for event in events:
            event_copy = event.copy()
            if "location" in event_copy and event_copy["location"]:
                # Use LLM to disambiguate location if needed
                full_location = self._disambiguate_location(event_copy["location"], city)
                coordinates = self._geocode_location(full_location)
                event_copy["coordinates"] = coordinates
                
                # Calculate influence zone based on event type
                event_copy["influence_radius"] = self._calculate_influence_radius(event_copy)
            
            tagged_events.append(event_copy)
        
        return tagged_events
    
    def _disambiguate_location(self, location, city):
        if city.lower() in location.lower():
            return location
            
        prompt = f"""
        Disambiguate this location reference: "{location}" within the city of {city}.
        Return only the full, specific location that would be recognized by a mapping service.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=100
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error in location disambiguation: {e}")
            return f"{location}, {city}"
    
    def _geocode_location(self, location):
        try:
            location_data = self.geolocator.geocode(location)
            if location_data:
                return (location_data.latitude, location_data.longitude)
        except (GeocoderTimedOut, GeocoderUnavailable) as e:
            print(f"Geocoding error for: {location}, {e}")
        
        return None
    
    def _calculate_influence_radius(self, event):
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
            
            response = self.client.chat.completions.create(
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