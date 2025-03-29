import pandas as pd
import json
import os
import openai
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Define default data directory and events file path
DEFAULT_DATA_DIR = "data"
_events_file = os.path.join(DEFAULT_DATA_DIR, "events.json")

# Ensure data directory exists
os.makedirs(DEFAULT_DATA_DIR, exist_ok=True)

def get_openai_client():
    """Get OpenAI client with API key from environment variables"""
    api_key = os.getenv("OPENAI_API_KEY")
    return openai.OpenAI(api_key=api_key)

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

def get_events(start_date=None, end_date=None, events_file=None):
    """
    Get events from storage, optionally filtered by date range
    Returns events as a list of dictionaries
    """
    if events_file is None:
        events_file = _events_file
    
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
    
    # Get OpenAI client
    client = get_openai_client()
    
    # Use LLM to convert to standard format
    date_mapping = {}
    for date_ref in date_refs:
        parsed_date = parse_date_with_llm(date_ref, client)
        date_mapping[date_ref] = parsed_date
    
    # Add parsed_date column
    df_copy = df.copy()
    df_copy["parsed_date"] = df_copy["date"].map(date_mapping)
    return df_copy

def parse_date_with_llm(date_text, client=None):
    """Parse a date reference using LLM to convert to a standard datetime object"""
    if client is None:
        client = get_openai_client()
        
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