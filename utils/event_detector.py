import json
import os

from dotenv import load_dotenv
from newspaper import Article
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

load_dotenv()

from openai import OpenAI

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)


def is_traffic_relevant(article: Dict[str, Any], city: str) -> bool:
    """
    Check if the article with given title and description
    contains news that could affect road traffic in the specified city.
    """

    prompt = f"""
    You are a news classifier with expertise in transportation impacts. An article is considered to have 'traffic-affecting news' if it reports events such as road accidents, major construction, severe weather conditions, public demonstrations, sports events, concerts, festivals, or similar incidents that could disrupt nearby road traffic. Otherwise, it is classified as 'non-traffic-affecting.

    Given the following article information. Can it effect traffic in {city}:
    
    Title: {article.get("title", "")}
    Description: {article.get("description", "")}
    
    Classify this article as either "Yes" (if it can affect traffic) or "No" (if it cannot affect traffic) and output your answer in JSON format as follows:

    {{ "affect_traffic": "Yes" }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)
        answer = result.get("affect_traffic", "No").lower()
        if answer == "yes":
            print(f"print from is_traffic_relevant: {article}")
        return answer == "yes"

    except Exception as e:
        print(f"Error checking traffic relevance: {e}")
        return False


class TrafficEvent(BaseModel):
    event_type: str
    location: str
    date: str
    time: Optional[str] = None
    scale: Optional[str] = None


def extract_event(article: Dict[str, Any], city: str) -> Optional[TrafficEvent]:
    """Extract structured event data from text using LLM"""

    city_context = f"Focus on events in or near {city}."
    text = f"Title: {article['title']}\nFull content: {article['full_content']}"

    prompt = f"""
    Extract events that can affect road traffic from this text. {city_context}
    For each event, provide:
    1. Event type (concert, sport event, road closure, construction, festival, etc.)
    2. Location (as specific as possible such as street name, pincode, landmark, etc. where this even is happening)
    3. Date (date at which this event is happening as specific as possible such as 01-01-2025 etc.)
    4. Time (Time at which this event is happening as specific as possible such as 10:00 AM, 10:00 PM etc.)
    5. Expected attendance or scale (if mentioned)
    
    If no traffic-related events are found in the text, return null.
    """

    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert at extracting traffic event information from news articles."},
                {"role": "user", "content": prompt + "\n\nText: " + text}
            ],
            response_format=TrafficEvent
        )
        
        if completion.choices[0].message.parsed is None:
            print("No traffic events found in the article")
            return None
            
        event = completion.choices[0].message.parsed
        print(f"--------------------------------")
        print(f"Extracted event: {event}")
        print(f"--------------------------------")
        return event
    except Exception as e:
        print(f"Error extracting event: {e}")
        return None


def fetch_full_content(url):
    """
    Fetch the full content of an article from its URL using newspaper3k
    """
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text
    except Exception as e:
        print(f"Error fetching content from URL {url}: {e}")
        return ""


def extract_event_from_article(article: Dict[str, Any], city: str) -> Dict[str, Any]:
    """
    Process an article to extract traffic-related events for a specific city.
    
    Process flow:
    1. Validates input article has required title and description
    2. Checks if article is traffic-relevant using LLM classification
    3. Fetches full content of relevant articles via newspaper3k
    4. Extracts structured event data using LLM from full content
    5. Attaches source article data to extracted events
    
    Args:
        article: Dictionary containing article data with title, description, and url
        city: Name of the city
        
    Returns:
        Dictionary containing structured event data with source article attached,
        or empty dictionary if article is not relevant or processing fails
    """
    
    title = article.get("title", "")
    description = article.get("description", "")

    # Skip articles without title or description
    if not title or not description:
        return {}

    # Check if article is traffic-relevant
    if not is_traffic_relevant(article, city):
        return {}

    # Fetch full content of the selected articles
    url = article.get("url", "")
    full_content = fetch_full_content(url)
    if not full_content:
        return {}
    
    article["full_content"] = full_content

    # Extract structured events from the article
    event = extract_event(article, city)
    if not event:
        return {}
    
    event_dict = event.model_dump()
    event_dict["source"] = article
    event_dict["city_name"] = city
    print(f"event: {event_dict}")

    return event_dict
