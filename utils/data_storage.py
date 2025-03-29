import json
import os
from datetime import datetime
from typing import Any, Dict, List

import openai
import pandas as pd
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


def load_events(events_file=None):
    """Load events from the JSON file or return empty DataFrame if file doesn't exist"""
    if events_file is None:
        events_file = _events_file
        
    if os.path.exists(events_file):
        try:
            return pd.read_json(events_file)
        except:
            return pd.DataFrame(columns=["event_type", "location", "date", "coordinates", 
                                       "influence_radius", "source", "created_at"])
    else:
        return pd.DataFrame(columns=["event_type", "location", "date", "coordinates", 
                                     "influence_radius", "source", "created_at"])

def save_events(events, events_file=None):
    """Save events to a JSON file with timestamps"""
    if events_file is None:
        events_file = _events_file
    
    # Get existing events
    existing_df = load_events(events_file)
    
    # Add timestamps to new events
    new_events = []
    for event in events:
        event_copy = event.copy()
        event_copy["created_at"] = datetime.now().isoformat()
        new_events.append(event_copy)
    
    # Combine existing and new events
    new_df = pd.DataFrame(new_events)
    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    
    # Save to file
    combined_df.to_json(events_file, orient="records")
    
    return combined_df

def get_events(start_date=None, end_date=None):
    """
    Get events from storage, optionally filtered by date range
    Returns events as a list of dictionaries
    """
    
    # Load events
    events_df = load_events(events_file)
    
    # If no date filtering or empty dataframe, return all
    if (not start_date and not end_date) or len(events_df) == 0:
        return events_df.to_dict("records")
    
    # Use LLM to standardize dates for comparison
    standardized_df = standardize_dates(events_df)
    
    # Filter by dates
    if start_date:
        standardized_df = standardized_df[standardized_df["parsed_date"] >= start_date]
    if end_date:
        standardized_df = standardized_df[standardized_df["parsed_date"] <= end_date]
    
    return standardized_df.to_dict("records")

def standardize_dates(df):
    """Standardize date references in events to enable date filtering"""
    # Extract all unique date references
    date_refs = df["date"].dropna().unique().tolist()
    # Use LLM to convert to standard format
    date_mapping = {}
    for date_ref in date_refs:
        parsed_date = parse_date_with_llm(date_ref, client)
        date_mapping[date_ref] = parsed_date
    
    # Add parsed_date column
    df_copy = df.copy()
    df_copy["parsed_date"] = df_copy["date"].map(date_mapping)
    return df_copy

def parse_date_with_llm(date_text: str) -> datetime.date:
    """Parse a date reference using LLM to convert to a standard datetime object"""
        
    if not date_text:
        return datetime.now().date()
        
    prompt = f"""
    Convert this date reference: "{date_text}" to an ISO format date (YYYY-MM-DD).
    Use today's date as reference for relative terms like "tomorrow" or "next week".
    Return only the date in YYYY-MM-DD format, nothing else.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=20
        )
        
        date_str = response.choices[0].message.content.strip()
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception as e:
        print(f"Error parsing date: {e}")
        return datetime.now().date()  # Fallback to today 

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