import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List

from dotenv import load_dotenv

load_dotenv()

from openai import OpenAI

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# Define default data directory and events file path
DEFAULT_DATA_DIR = "data"
EXTRACTED_CITY_DATA_DIR = os.path.join(DEFAULT_DATA_DIR, "extracted_city_data")

# Ensure data directories exist
os.makedirs(DEFAULT_DATA_DIR, exist_ok=True)
os.makedirs(EXTRACTED_CITY_DATA_DIR, exist_ok=True)

def clean_id_component(text: str) -> str:
    """
    Clean a string for use in an ID by:
    - Converting to lowercase
    - Replacing spaces with underscores
    - Removing special characters
    
    Args:
        text (str): Text to clean
        
    Returns:
        str: Cleaned text suitable for use in an ID
    """
    cleaned = text.lower().replace(' ', '_')
    cleaned = re.sub(r'[^\w]', '', cleaned)
    
    return cleaned

def get_event_id(event: Dict[str, Any]) -> str:
    """
    Generate a unique ID for an event by cleaning and combining its attributes.
    
    Args:
        event (Dict[str, Any]): Event dictionary containing at least event_type, location, and start_date
        
    Returns:
        str: A unique ID string for the event
    """
    event_type = clean_id_component(event.get('event_type', 'unknown'))
    location = clean_id_component(event.get('location', 'unknown'))
    
    # Use start_date if available, otherwise try date
    date_field = event.get('start_date') or event.get('date', 'unknown')
    date = clean_id_component(date_field)
    
    return f"{event_type}_{location}_{date}"


def save_city_events(events: List[Dict[str, Any]], 
                     country_code: str, city_name: str) -> str:
    """
    Save extracted events for a specific city to a JSON file in the extracted_city_data directory.
    The file is named using the country_code and city_name: country-code_city_name.json
    
    Args:
        events (list): List of event dictionaries to save
        country_code (str): Three-letter country code
        city_name (str): Name of the city
        
    Returns:
        str: Path to the saved file
    """
    if not events:
        return None
        
    # Create a clean filename: country-code_city_name.json
    # Replace spaces with underscores and convert to lowercase
    clean_city_name = city_name.replace(" ", "_").lower()
    filename = f"{country_code.lower()}_{clean_city_name}.json"
    file_path = os.path.join(EXTRACTED_CITY_DATA_DIR, filename)
    
    # Load existing events if the file exists
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                existing_events = json.load(f)
        except Exception as e:
            print(f"Error reading existing city data: {e}")
            existing_events = []
    else:
        existing_events = []
    
    # Create a set of existing event IDs
    existing_event_ids = {event['id'] for event in existing_events}
    
    # Add timestamps and IDs to new events, only if the ID is not already present
    events_with_timestamp = []
    for event in events:
        event_copy = event.copy()
        event_copy["created_at"] = datetime.now().isoformat()
        
        # Make sure the country code is included
        if "country_code" not in event_copy:
            event_copy["country_code"] = country_code
            
        # Generate a unique ID for the event
        event_copy["id"] = get_event_id(event)
        
        # Append only if the ID is not in existing_event_ids
        if event_copy["id"] not in existing_event_ids:
            events_with_timestamp.append(event_copy)
    
    # Combine existing and new events
    combined_events = existing_events + events_with_timestamp
    
    # Save to file (overwrite with combined data)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(combined_events, f, indent=2)
    
    return file_path

def get_city_events(country_code: str, city_name: str, start_date: datetime.date, end_date: datetime.date) -> List[Dict[str, Any]]:
    """
    Get saved events for a specific city from the extracted_city_data directory.
    
    Args:
        country_code (str): Three-letter country code
        city_name (str): Name of the city
        start_date (datetime or str, optional): Filter events on or after this date (DD-MM-YYYY format)
        end_date (datetime or str, optional): Filter events on or before this date (DD-MM-YYYY format)
        
    Returns:
        list: List of event dictionaries, or empty list if file doesn't exist
    """
    clean_city_name = city_name.replace(" ", "_").lower()
    filename = f"{country_code.lower()}_{clean_city_name}.json"
    file_path = os.path.join(EXTRACTED_CITY_DATA_DIR, filename)
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                events = json.load(f)
                filtered_events = []

                for event in events:
                    # Get event start and end dates
                    event_start_date = event.get('start_date')
                    event_end_date = event.get('end_date')
                    
                    if not event_start_date:
                        continue

                    event_start_date_obj = datetime.strptime(event_start_date, "%d-%m-%Y").date()
                    event_end_date_obj = datetime.strptime(event_end_date, "%d-%m-%Y").date()

                    if event_start_date_obj > end_date:
                        continue
                    if event_end_date_obj < start_date:
                        continue
                            
                    filtered_events.append(event)

                return filtered_events

        except Exception as e:
            print(f"Error reading city data: {e}")
            return []
    else:
        return []
