import json
import os
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
        event_copy["country_code"] = country_code
        event_copy["id"] = f"{event['event_type']}_{event['location']}_{event['date']}"
        
        # Append only if the ID is not in existing_event_ids
        if event_copy["id"] not in existing_event_ids:
            events_with_timestamp.append(event_copy)
    
    # Combine existing and new events
    combined_events = existing_events + events_with_timestamp
    
    # Save to file (overwrite with combined data)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(combined_events, f, indent=2)
    
    return file_path

def get_city_events(country_code: str, city_name: str) -> List[Dict[str, Any]]:
    """
    Get saved events for a specific city from the extracted_city_data directory.
    
    Args:
        country_code (str): Three-letter country code
        city_name (str): Name of the city
        
    Returns:
        list: List of event dictionaries, or empty list if file doesn't exist
    """
    clean_city_name = city_name.replace(" ", "_").lower()
    filename = f"{country_code.lower()}_{clean_city_name}.json"
    file_path = os.path.join(EXTRACTED_CITY_DATA_DIR, filename)
    
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading city data: {e}")
            return []
    else:
        return []
