import os
import json
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional
from openai import OpenAI
from datetime import datetime, date

load_dotenv()

# Initialize the OpenAI client with API key from environment
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def find_traffic_events(city: str, country: str, days: Optional[int] = 7, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[Dict[str, Any]]:
    """
    Find events that could affect road traffic in the specified city using OpenAI with web search.
    
    Args:
        city: Name of the city to search for events
        country: Country code for localization
        days: Number of days ahead to search for events (default: 7)
        start_date: Optional start date for custom date range
        end_date: Optional end date for custom date range
        
    Returns:
        List of structured event dictionaries
    """
    # Define the web search tool
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

    # Create the search prompt based on the provided date parameters
    if start_date and end_date:
        # Format dates for display
        start_str = start_date.strftime('%d-%m-%Y')
        end_str = end_date.strftime('%d-%m-%Y')
        search_prompt = f"Find events in {city} that could affect road traffic between {start_str} and {end_str}."
    else:
        # Default to days ahead
        search_prompt = f"Find events in {city} that could affect road traffic in the next {days} days."

    # Prepare the conversation messages
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant that extracts event information from text and returns it in a structured JSON format. "
                "When extracting events that could affect road traffic (e.g., concerts, sports events, road closures, construction, festivals, public protests, etc.), "
                "include the following details for each event: "
                "- Event type (e.g., concert, sport event, road closure, construction, festival, public protest) "
                "- Event name (if mentioned, otherwise null) "
                "- Location (as specific as possible, including venue, street name, locality, landmark, city, etc.) "
                "- Date (in DD-MM-YYYY format, as specific as possible) "
                "- Start time (e.g., 10:00 AM or 10:00 PM, as specific as possible) "
                "- End time (e.g., 10:00 AM or 10:00 PM, as specific as possible) "
                "- Expected traffic impact (low, medium, or high, inferred if not explicitly stated) "
                "- Source (the specific web page or article where the information is found) "
                "If the start time is not specified and the event is likely to occur in the evening (e.g., concerts, festivals), "
                "assume a start time of 18:00. If no traffic-related events are found, return null."
            )
        },
        {
            "role": "user",
            "content": search_prompt
        }
    ]

    try:
        # Create the response using the new responses.create endpoint
        response = client.responses.create(
            model="gpt-4o",
            input=messages,
            tools=tools,
            tool_choice={"type": "web_search_preview"},
            text={
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
                                        "date": {"type": "string"},
                                        "start_time": {"type": "string"},
                                        "end_time": {"type": "string"},
                                        "traffic_impact": {"type": "string", "enum": ["low", "medium", "high"]},
                                        "source": {"type": "string"}
                                    },
                                    "required": ["event_type", "event_name", "location", "date", "start_time", "end_time", "traffic_impact", "source"],
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
        )
        
        # Parse the response - field name changes with new endpoint
        events_json = response.output_text
        events_data = json.loads(events_json) if events_json else {"events": []}
        events = events_data.get("events", []) if events_data else []
        
        # Return empty list if null is returned
        if events is None:
            return []
        
        print("--------------------------------")
        print(f"Found {len(events)} events. {events}")
        print("--------------------------------")
        return events
        
    except Exception as e:
        print(f"Error finding traffic events: {e}")
        return []
