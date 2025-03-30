import os
import json
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from openai import OpenAI

load_dotenv()

# Initialize the OpenAI client with API key from environment
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def find_traffic_events(city: str, country: str, days: int = 7) -> List[Dict[str, Any]]:
    """
    Find events that could affect road traffic in the specified city using OpenAI with web search.
    
    Args:
        city: Name of the city to search for events
        country: Country code for localization
        days: Number of days ahead to search for events (default: 7)
        
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
            "content": f"Find events in {city} that could affect road traffic in the next {days} days."
        }
    ]

    try:
        # Create the response using the new responses.create endpoint
        response = client.responses.create(
            model="o3-mini",
            input=messages,
            tools=tools,
            tool_choice={"type": "web_search_preview"},
            reasoning={"effort": "high"},
            text={
                "format": {
                    "type": "json_schema",
                    "name": "event_list",
                    "schema": {
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
                            "required": ["event_type", "location", "date", "start_time", "end_time", "traffic_impact", "source"],
                            "additionalProperties": False
                        }
                    },
                    "strict": True
                }
            }
        )
        
        # Parse the response - field name changes with new endpoint
        events_json = response.output_text
        events = json.loads(events_json) if events_json else []
        
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
