import os
import json
from utils.news_fetcher import fetch_news, generate_mock_data_for_city
from utils.event_detector import detect_events_by_city

def main():
    # Get city from user
    city = input("Enter a city name to detect traffic events: ")
    
    print(f"\nFetching news for {city}...")
    
    # Fetch news with city in the query
    query = f"{city} AND (traffic OR construction OR road OR concert OR event OR festival)"
    
    # Try to fetch real news, fallback to mock data if API key not available
    try:
        articles = fetch_news(query=query, days=14)
        if not articles:
            print("No articles found or API key issue. Generating mock data...")
            articles = generate_mock_data_for_city(city, num_articles=10)
    except Exception as e:
        print(f"Error fetching news: {e}")
        print("Using mock data instead...")
        articles = generate_mock_data_for_city(city, num_articles=10)
    
    print(f"Found {len(articles)} news articles for {city}")
    
    # Detect traffic-relevant events
    events = detect_events_by_city(articles, city)
    
    # Display results
    if events:
        print(f"\nDetected {len(events)} traffic-related events in {city}:")
        for i, event in enumerate(events, 1):
            print(f"\nEvent #{i}:")
            print(f"Type: {event.get('event_type', 'Unknown')}")
            print(f"Location: {event.get('location', 'Unknown')}")
            print(f"Date: {event.get('date', 'Unknown')}")
            print(f"Time: {event.get('time', 'Unknown')}")
            print(f"Scale: {event.get('scale', 'Unknown')}")
            source = event.get('source', {})
            print(f"Source: {source.get('source', {}).get('name', 'Unknown')}")
    else:
        print(f"\nNo traffic-related events detected in {city}")

if __name__ == "__main__":
    main() 