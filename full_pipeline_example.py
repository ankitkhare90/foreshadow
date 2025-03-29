import os
import json
from utils.news_fetcher import fetch_news, generate_mock_data_for_city
from utils.event_detector import detect_events_by_city
from utils.geo_tagger import geo_tag_events
from utils.data_storage import save_events, get_events
from datetime import datetime, timedelta

def run_full_pipeline(city, days=7, save_to_storage=True):
    """
    Run the complete pipeline to:
    1. Fetch news for a city
    2. Detect traffic-relevant events
    3. Add geographic coordinates
    4. Save to storage (optional)
    5. Return the processed events
    """
    print(f"Step 1: Fetching news for {city}...")
    
    # Construct query with city name and traffic-related terms
    query = f"{city} AND (traffic OR construction OR road OR concert OR event OR festival)"
    
    # Try to fetch real news, fallback to mock data
    try:
        articles = fetch_news(query=query, days=days)
        if not articles:
            print("No articles found or API key issue. Generating mock data...")
            articles = generate_mock_data_for_city(city, num_articles=10)
    except Exception as e:
        print(f"Error fetching news: {e}")
        print("Using mock data instead...")
        articles = generate_mock_data_for_city(city, num_articles=10)
    
    print(f"Found {len(articles)} news articles for {city}")
    
    # Step 2: Detect traffic-relevant events
    print("\nStep 2: Analyzing articles for traffic relevance...")
    events = detect_events_by_city(articles, city)
    
    if not events:
        print("No traffic-relevant events detected")
        return []
    
    print(f"Detected {len(events)} traffic-relevant events")
    
    # Step 3: Add geographic coordinates
    print("\nStep 3: Adding geographic coordinates...")
    geo_tagged_events = geo_tag_events(events, city)
    
    # Step 4: Save to storage if requested
    if save_to_storage:
        print("\nStep 4: Saving events to storage...")
        save_events(geo_tagged_events)
        print("Events saved successfully")
    
    return geo_tagged_events

def main():
    # Get city from user
    city = input("Enter a city name to process: ")
    
    # Run the pipeline
    events = run_full_pipeline(city)
    
    # Display results
    if events:
        print(f"\nSummary of {len(events)} events in {city}:")
        for i, event in enumerate(events, 1):
            print(f"\nEvent #{i}:")
            print(f"Type: {event.get('event_type', 'Unknown')}")
            print(f"Location: {event.get('location', 'Unknown')}")
            print(f"Coordinates: {event.get('coordinates', 'Unknown')}")
            print(f"Date: {event.get('date', 'Unknown')}")
            print(f"Time: {event.get('time', 'Unknown')}")
            print(f"Scale: {event.get('scale', 'Unknown')}")
            print(f"Influence radius: {event.get('influence_radius', 'Unknown')} km")
            
        # Demonstrate retrieval from storage
        print("\nRetrieving events from storage:")
        stored_events = get_events()
        print(f"Retrieved {len(stored_events)} events from storage")
        
    else:
        print(f"\nNo traffic-related events detected in {city}")

if __name__ == "__main__":
    main() 