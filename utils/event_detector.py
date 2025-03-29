
import json
import os

from dotenv import load_dotenv
from newspaper import Article
from typing import Dict, Any, List

load_dotenv()

from openai import OpenAI

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)


def is_traffic_relevant(title: str, description: str, city: str) -> bool:
    """
    Check if the article with given title and description
    contains news that could affect road traffic in the specified city.
    """

    prompt = f"""
    You are a news classifier with expertise in transportation impacts. An article is considered to have 'traffic-affecting news' if it reports events such as road accidents, major construction, severe weather conditions, public demonstrations, sports events, concerts, festivals, or similar incidents that could disrupt nearby road traffic. Otherwise, it is classified as 'non-traffic-affecting.

    Given the following article information. Can it effect traffic in {city}:
    
    Title: {title}
    Description: {description}
    
    Classify this article as either "Yes" (if it can affect traffic) or "No" (if it cannot affect traffic) and output your answer in JSON format as follows:

    {{ "affect_traffic": "Yes" }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.01,
            max_tokens=2048,
        )

        result = json.loads(response.choices[0].message.content)
        print(result)
        answer = result.get("affect_traffic", "No").lower()
        return answer == "yes"

    except Exception as e:
        print(f"Error checking traffic relevance: {e}")
        return False


def extract_event(article: Dict[str, Any], city: str) -> List[Dict[str, Any]]:
    """Extract structured event data from text using LLM"""

    city_context = f"Focus on events in or near {city}."
    text = f"Title: {article['title']}.
    Full content: {article['full_content']}"

    prompt = f"""
    Extract events that can affect road traffic from this text. {city_context}
    For each event, provide:
    1. Event type (concert, sport event, road closure, construction, festival, etc.)
    2. Location (as specific as possible such as street name, pincode, landmark, etc. where this even is happening)
    3. Date (date at which this event is happening as specific as possible such as 01-01-2025 etc.)
    4. Time (Time at which this event is happening as specific as possible such as 10:00 AM, 10:00 PM etc.)
    5. Expected attendance or scale (if mentioned)
    
    Return JSON format only, with no explanation:
    [
      {{
        "event_type": "...",
        "location": "...",
        "date": "...",
        "time": "...",
        "scale": "..."
      }}
    ]
    
    If no traffic-related events are found, return an empty array.
    
    Text: {text}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=2048,
        )

        return json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        print("Error parsing JSON response from LLM")
        return []
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return []


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
    if not is_traffic_relevant(title, description, city):
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
    
    event["source"] = article
    event["city"] = city

    return event
