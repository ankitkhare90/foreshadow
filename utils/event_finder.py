import json
import os
from typing import Any, Dict, List

import streamlit as st
from openai import OpenAI

from utils.date_utils import (
    parse_date, format_date, 
    do_date_ranges_overlap, validate_event_dates
)

# Initialize the OpenAI client with API key from session state
def get_openai_client():
    if st.session_state.openai_api_key:
        return OpenAI(api_key=st.session_state.openai_api_key)
    else:
        return None

def validate_event_date(event: Dict[str, Any], search_start_date: str, search_end_date: str) -> Dict[str, Any]:
    """
    Validates the start_date and end_date of an event and sets defaults if invalid.
    Also filters out events that don't overlap with the search date range.
    
    Args:
        event: Event dictionary containing event details
        search_start_date: Start date of the search range (DD-MM-YYYY or date object)
        search_end_date: End date of the search range (DD-MM-YYYY or date object)
        
    Returns:
        The event dictionary with validated date fields or empty dict if invalid or outside search range
    """
    
    try:
        # Process the event dates
        event = validate_event_dates(event)
        
        # Get event date objects
        if not event.get("start_date"):
            print(f"No start_date provided for event: {event}")
            return {}
            
        start_date_obj = parse_date(event["start_date"])
        if not start_date_obj:
            print(f"Invalid start_date: {event['start_date']}")
            return {}
            
        end_date_obj = parse_date(event["end_date"])
        if not end_date_obj:
            # If end_date is invalid but start_date is valid, use start_date as end_date
            event["end_date"] = event["start_date"]
            end_date_obj = start_date_obj
        
        # Check if end date is before start date (invalid)
        if end_date_obj < start_date_obj:
            print(f"Invalid date range: end date {end_date_obj} is before start date {start_date_obj}")
            return {}
        
        # Convert search dates to date objects if they are strings
        search_start_date_obj = search_start_date
        if isinstance(search_start_date, str):
            search_start_date_obj = parse_date(search_start_date)
            if not search_start_date_obj:
                return {}
        
        search_end_date_obj = search_end_date
        if isinstance(search_end_date, str):
            search_end_date_obj = parse_date(search_end_date)
            if not search_end_date_obj:
                return {}
        
        # Debug log the actual dates being compared 
        print(f"Comparing event ({start_date_obj} to {end_date_obj}) with search range ({search_start_date_obj} to {search_end_date_obj})")
        
        # Check if event overlaps with search date range
        if not do_date_ranges_overlap(
            start_date_obj, end_date_obj,
            search_start_date_obj, search_end_date_obj
        ):
            print(f"Event date range ({start_date_obj} to {end_date_obj}) doesn't overlap with search range ({search_start_date_obj} to {search_end_date_obj})")
            return {}
            
    except Exception as e:
        print(f"Error validating event date: {e}")
        return {}
    
    return event


def validate_event_time(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates the start_time and end_time of an event and sets defaults if invalid.
    
    Args:
        event: Event dictionary containing event details
        
    Returns:
        The event dictionary with validated time fields
    """
    # Use the full event date validation from date_utils instead
    return validate_event_dates(event)

text_format = {
                    "format": {
                        "type": "json_schema",
                        "name": "event_list",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "events": {
                                    "type": ["array", "null"],
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "event_type": {"type": "string"},
                                            "event_name": {"type": ["string", "null"]},
                                            "location": {"type": "string"},
                                            "start_date": {"type": "string"},
                                            "end_date": {"type": "string"},
                                            "start_time": {"type": "string"},
                                            "end_time": {"type": "string"},
                                            "traffic_impact": {"type": "string", "enum": ["low", "medium", "high"]},
                                            "source": {"type": "string"}
                                        },
                                        "required": ["event_type", "event_name", "location", "start_date", "end_date", "start_time", "end_time", "traffic_impact", "source"],
                                        "additionalProperties": False
                                    }
                                }
                            },
                            "required": ["events"],
                            "additionalProperties": False
                        },
                        "strict": True
                    }
                }

def get_prompt(city: str, country: str, event_type: str,  start_date: str,  end_date: str) -> str:
    """
    Generate a prompt for finding traffic events in a specific city and country.
    """
    prompt = f"""You are a helpful assistant that finds {event_type} events information from internet and returns it in a structured JSON format. 
        Find {event_type} events in {city} {country} between {start_date} and {end_date}.

        Extract following details for each event: 
        - Event type (e.g., concert, sport event, road closure, construction, festival, public protest) 
        - Event name (if mentioned, otherwise null) 
        - Location (as specific as possible, including venue, street name, locality, landmark, city, etc.) 
        - Start Date: Date on which the event is likely to start (in DD-MM-YYYY format, as specific as possible)
        - End Date: Date on which the event is likely to end (in DD-MM-YYYY format, as specific as possible)
        - Start Time: Time on which the event is likely to start (e.g., 10:00 AM or 10:00 PM, as specific as possible) 
        - End Time: Time on which the event is likely to end (e.g., 10:00 AM or 10:00 PM, as specific as possible) 
        - Expected traffic impact (low, medium, or high, inferred if not explicitly stated) 
        - Source (the specific web page or article where the information is found) 
        If the start time is not specified and the event is likely to occur in the evening (e.g., concerts, live shows,festivals), assume a start time of 18:00. 
        IMPORTANT: Start Date is very important, so make sure to always include it for every event.
    """
    return prompt

def find_traffic_events(city: str, country: str,
                        start_date, end_date, event_type: str) -> List[Dict[str, Any]]:
    """
    Find events that could affect road traffic in the specified city using OpenAI with web search.
    
    Args:
        city: Name of the city to search for events
        country: Country code for localization
        start_date: start date for custom date range (in DD-MM-YYYY format or date object)
        end_date: end date for custom date range (in DD-MM-YYYY format or date object)
        
    Returns:
        List of structured event dictionaries
    """
    # Convert dates to strings in our standard format
    if hasattr(start_date, 'strftime'):
        start_date = format_date(start_date)
    
    if hasattr(end_date, 'strftime'):
        end_date = format_date(end_date)
        
    # Get OpenAI client using API key from session state
    client = get_openai_client()
    
    # Check if API key is provided
    if not client:
        st.error("Please enter your OpenAI API key in the sidebar to search for events.")
        return []
    
    # Check if API key format is valid (simple check)
    if not st.session_state.openai_api_key.startswith("sk-"):
        st.warning("The OpenAI API key format doesn't look valid. It should start with 'sk-'.")

    tools = [
        {
            "type": "web_search_preview",
            "search_context_size": "high",
            "user_location": {
                "type": "approximate",
                "country": country,
                "city": city
            }
        }
    ]

    # Set maximum retry count and initialize current attempt
    max_retries = 2
    attempt = 0
    events = []
    
    while attempt < max_retries:
        attempt += 1
        
        try:
            if attempt > 1:
                print(f"Retry attempt {attempt}/{max_retries} for event type: {event_type}")
                st.info(f"Retrying search attempt {attempt}/{max_retries} for {event_type}...")
                
            response = client.responses.create(
                model="gpt-4o",
                input = [
                    {
                        "role": "user",
                        "content": get_prompt(city, country, event_type, start_date, end_date)
                    }
                ],
                tools=tools,
                tool_choice={"type": "web_search_preview"},
                text=text_format
            )

            # Parse the response - field name changes with new endpoint
            events_json = response.output_text
            print(f"--------------------------------    ")
            print(f"Events JSON: {events_json}")
            print(f"--------------------------------")
            try:
                events_data = json.loads(events_json) if events_json else {"events": []}
                events = events_data.get("events", []) if events_data else []
                print(f"Found {len(events)} events for event type: {event_type}")
                # JSON parsing succeeded, break out of the retry loop
                break
            except json.JSONDecodeError as json_err:
                print(f"Error parsing JSON response for event type: {event_type}. Error: {json_err}")
                if attempt < max_retries:
                    print(f"Will retry, {max_retries - attempt} attempts remaining")
                    continue
                else:
                    print(f"Maximum retry attempts reached. Unable to parse JSON response.")
                    events = []
                    break

        except Exception as e:
            print(f"Error finding traffic events: {e} for event type: {event_type}")
            error_message = str(e).lower()
            
            # Check for authentication/API key errors
            if "auth" in error_message or "api key" in error_message or "authentication" in error_message or "invalid" in error_message or "unauthorized" in error_message:
                st.error(f"Authentication error: Your OpenAI API key appears to be invalid. Please check your API key and try again.")
            elif "quota" in error_message or "billing" in error_message or "exceeded" in error_message:
                st.error(f"OpenAI API usage limit reached: Your account may be out of credits or has exceeded its quota.")
            else:
                st.error(f"Error finding traffic events: {e}")
            return []

    events = [validate_event_time(event) for event in events]
    events = [validate_event_date(event, start_date, end_date) for event in events]
    events = [event for event in events if event]
    
    return events
