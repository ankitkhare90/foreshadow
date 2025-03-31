import json
import os
from typing import Any, Dict, List

import streamlit as st
from dateutil import parser as date_parser
from openai import OpenAI

# Initialize the OpenAI client with API key from environment
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

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
        start_date_obj = None
        
        if event.get("start_date"):
            try:
                start_date_obj = date_parser.parse(event["start_date"], fuzzy=True).date()
                event["start_date"] = start_date_obj.strftime("%d-%m-%Y")
            except (ValueError, TypeError):
                print(f"Invalid start_date: {event['start_date']}")
                return {}
        else:
            print(f"No start_date provided for event: {event}")
            return {}

        # Handle end_date
        end_date_obj = None
        if event.get("end_date"):
            try:
                end_date_obj = date_parser.parse(event["end_date"], fuzzy=True).date()
                event["end_date"] = end_date_obj.strftime("%d-%m-%Y")
            except:
                event["end_date"] = event.get("start_date")
                end_date_obj = start_date_obj
        else:
            event["end_date"] = event["start_date"]
            end_date_obj = start_date_obj
        
        # Check if end date is before start date (invalid)
        if end_date_obj < start_date_obj:
            print(f"Invalid date range: end date {end_date_obj} is before start date {start_date_obj}")
            return {}
        
        # Parse search date range - handle both string and date object inputs
        search_start_date_obj = search_start_date
        if isinstance(search_start_date, str):
            search_start_date_obj = date_parser.parse(search_start_date, fuzzy=True).date()
        
        search_end_date_obj = search_end_date
        if isinstance(search_end_date, str):
            search_end_date_obj = date_parser.parse(search_end_date, fuzzy=True).date()
        
        # Check if event overlaps with search date range
        # Event overlaps if: event_start <= search_end AND event_end >= search_start
        if start_date_obj > search_end_date_obj or end_date_obj < search_start_date_obj:
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
    try:
        # Handle start_time
        if event.get("start_time"):
            try:
                # Use dateutil.parser to automatically detect the time format
                time_obj = date_parser.parse(event["start_time"], fuzzy=True)
                # Convert to 12-hour format
                event["start_time"] = time_obj.strftime("%I:%M %p")
            except (ValueError, TypeError):
                print(f"Invalid start_time: {event['start_time']}")
                event["start_time"] = "12:00 AM"
        else:
            # No start_time provided
            event["start_time"] = "12:00 AM"

        # Handle end_time
        if event.get("end_time"):
            try:
                # Use dateutil.parser to automatically detect the time format
                time_obj = date_parser.parse(event["end_time"], fuzzy=True)
                # Convert to 12-hour format
                event["end_time"] = time_obj.strftime("%I:%M %p")
            except (ValueError, TypeError):
                event["end_time"] = "11:59 PM"
        else:
            # No end_time provided
            event["end_time"] = "11:59 PM"
            
    except Exception:
        # Fallback for any unexpected errors
        event["start_time"] = "12:00 AM"
        event["end_time"] = "11:59 PM"
    
    return event

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
        days: Number of days ahead to search for events (default: 7)
        start_date: start date for custom date range (in DD-MM-YYYY format or date object)
        end_date: end date for custom date range (in DD-MM-YYYY format or date object)
        
    Returns:
        List of structured event dictionaries
    """
    # Convert dates to strings if they are date objects
    if hasattr(start_date, 'strftime'):
        start_date = start_date.strftime("%d-%m-%Y")
    
    if hasattr(end_date, 'strftime'):
        end_date = end_date.strftime("%d-%m-%Y")

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

    try:
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
        events_data = json.loads(events_json) if events_json else {"events": []}
        events = events_data.get("events", []) if events_data else []
        print(f"Found {len(events)} events for event type: {event_type}")

    except Exception as e:
        print(f"Error finding traffic events: {e} for event type: {event_type}")
        return []

    events = [validate_event_time(event) for event in events]
    events = [validate_event_date(event, start_date, end_date) for event in events]
    events = [event for event in events if event]
    
    return events
