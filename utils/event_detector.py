import openai
import os
import json
from dotenv import load_dotenv

load_dotenv()

def get_openai_client():
    """Get OpenAI client with API key from environment variables"""
    api_key = os.getenv("OPENAI_API_KEY")
    return openai.OpenAI(api_key=api_key)

def is_traffic_relevant(title, description, city, client=None):
    """
    Check if the article with given title and description 
    contains news that could affect road traffic in the specified city.
    """
    if client is None:
        client = get_openai_client()
    
    prompt = f"""
    Does this news article contain information about events that could affect road traffic in {city}?
    
    Title: {title}
    Description: {description}
    
    Answer only with 'Yes' or 'No'.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=10,
        )
        
        answer = response.choices[0].message.content.strip().lower()
        return answer == 'yes' or answer == 'yes.'
        
    except Exception as e:
        print(f"Error checking traffic relevance: {e}")
        return False

def extract_events_with_llm(text, city=None, client=None):
    """Extract structured event data from text using LLM"""
    if client is None:
        client = get_openai_client()
    
    city_context = f"Focus on events in or near {city}. " if city else ""
    
    prompt = f"""
    Extract traffic-related events from this text. {city_context}For each event, provide:
    1. Event type (concert, sport event, road closure, construction, festival, etc.)
    2. Location (as specific as possible such as street name, pincode, landmark, etc.)
    3. Date (as specific as possible such as 01-01-2025 etc.)
    4. Time (as specific as possible such as 10:00 AM, 10:00 PM, etc.)
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

def detect_events_by_city(articles, city):
    """
    Filter articles by city and detect traffic-relevant events in two phases:
    1. First check if each article is traffic-relevant
    2. Then extract structured events from relevant articles
    """
    # Get OpenAI client once and reuse
    client = get_openai_client()
    
    # Filter relevant articles first
    relevant_articles = []
    
    for article in articles:
        title = article.get('title', '')
        description = article.get('description', '')
        
        # Skip articles without title or description
        if not title or not description:
            continue
            
        # Check if article is traffic-relevant
        if is_traffic_relevant(title, description, city, client):
            relevant_articles.append(article)
    
    # Process relevant articles for structured event data
    events = []
    for article in relevant_articles:
        title = article.get('title', '')
        content = article.get('content', '')
        
        # If content is missing, fall back to description
        if not content:
            content = article.get('description', '')
            
        # Extract structured events from the article
        article_text = f"{title}. {content}"
        events_from_article = extract_events_with_llm(article_text, city, client)
        
        # Add source information to each event
        for event in events_from_article:
            event["source"] = article
            
        events.extend(events_from_article)
        
    return events

def detect_events(articles):
    """Legacy function maintained for backward compatibility"""
    client = get_openai_client()
    events = []
    for article in articles:
        content = f"{article['title']}. {article['description']}"
        events_from_article = extract_events_with_llm(content, client=client)
        for event in events_from_article:
            event["source"] = article
        events.extend(events_from_article)
    return events
