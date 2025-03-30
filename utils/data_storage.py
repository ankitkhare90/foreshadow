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
        event (Dict[str, Any]): Event dictionary containing at least event_type, location, and date
        
    Returns:
        str: A unique ID string for the event
    """
    event_type = clean_id_component(event['event_type'])
    location = clean_id_component(event['location'])
    date = clean_id_component(event['date'])
    
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

def get_city_events(country_code: str, city_name: str, start_date=None, end_date=None) -> List[Dict[str, Any]]:
    """
    Get saved events for a specific city from the extracted_city_data directory.
    
    Args:
        country_code (str): Three-letter country code
        city_name (str): Name of the city
        start_date (datetime or str, optional): Filter events on or after this date
        end_date (datetime or str, optional): Filter events on or before this date
        
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
                
                # If date filtering is requested
                if start_date or end_date:
                    filtered_events = []
                    
                    # Convert string dates to datetime objects if needed
                    if start_date and isinstance(start_date, str):
                        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
                    if end_date and isinstance(end_date, str):
                        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
                    
                    for event in events:
                        event_date = event.get('date')
                        if not event_date:
                            continue
                            
                        # Try to parse the event date
                        try:
                            # Handle different date formats
                            try:
                                event_date_obj = datetime.strptime(event_date, "%Y-%m-%d").date()
                            except ValueError:
                                try:
                                    event_date_obj = datetime.strptime(event_date, "%d-%m-%Y").date()
                                except ValueError:
                                    event_date_obj = datetime.strptime(event_date, "%d/%m/%Y").date()
                                    
                            # Check date range
                            if start_date and event_date_obj < start_date:
                                continue
                            if end_date and event_date_obj > end_date:
                                continue
                                
                            # Event is within range, include it
                            filtered_events.append(event)
                        except ValueError:
                            # If we can't parse the date, include the event to be safe
                            filtered_events.append(event)
                    
                    return filtered_events
                
                return events
        except Exception as e:
            print(f"Error reading city data: {e}")
            return []
    else:
        return []
