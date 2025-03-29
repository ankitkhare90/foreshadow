import streamlit as st
import json
from utils.news_fetcher import fetch_news, generate_mock_data_for_city
from utils.event_detector import detect_events_by_city
from utils.location_utils import get_country_options, get_cities_for_country
from utils.data_storage import save_city_events, get_city_events
import pandas as pd
import os

st.set_page_config(
    page_title="Foreshadow - Traffic Event Detector",
    page_icon="🚦",
    layout="wide"
)

st.title("🚦 Foreshadow: Traffic Event Detector")
st.subheader("Detect traffic-affecting events in your city")

# Sidebar
with st.sidebar:
    st.header("About")
    st.write("""
    This application detects events that could affect traffic in a specified city.
    It uses a two-step process:
    1. Identify news articles relevant to traffic in the city
    2. Extract structured event information from relevant articles
    """)
    
    st.header("How it works")
    st.write("""
    1. Select a country and city
    2. The app searches for news about that city
    3. AI identifies which news could affect traffic
    4. For relevant news, AI extracts structured event details
    5. Data is saved for future reference
    """)

# Main content area
# Country selection
country_options = get_country_options()
country_code, country_name = st.selectbox(
    "Select a country:",
    options=country_options,
    format_func=lambda x: x[1],  # Display country name
    index=0
)

# City selection based on country
cities = get_cities_for_country(country_code)
if cities:
    city = st.selectbox("Select a city:", options=cities)
else:
    city = st.text_input("Enter a city name (no predefined cities available for this country):", placeholder="e.g., San Francisco")

days = st.slider("Days of news to search:", min_value=1, max_value=30, value=7)

# Check if we have saved data for this city
existing_events = get_city_events(country_code, city)
if existing_events:
    st.info(f"Found {len(existing_events)} previously saved events for {city}. You can search for new events or view existing data.")
    
    view_saved = st.button("View Saved Events", type="secondary")
    if view_saved:
        # Display saved events
        st.success(f"Showing {len(existing_events)} saved events for {city}")
        
        # Convert to DataFrame for display
        events_list = []
        for event in existing_events:
            event_dict = {
                "Type": event.get('event_type', 'Unknown'),
                "Location": event.get('location', 'Unknown'),
                "Date": event.get('date', 'Unknown'),
                "Time": event.get('time', 'Unknown'),
                "Scale": event.get('scale', 'Unknown'),
                "Source": event.get('source', {}).get('source', {}).get('name', 'Unknown')
            }
            events_list.append(event_dict)
        
        if events_list:
            df = pd.DataFrame(events_list)
            st.dataframe(df, use_container_width=True)
            
            # Also display as cards for better visualization
            st.subheader("Events Detail View")
            cols = st.columns(3)
            
            for i, event in enumerate(existing_events):
                with cols[i % 3]:
                    st.markdown(f"""
                    **Event Type**: {event.get('event_type', 'Unknown')}  
                    **Location**: {event.get('location', 'Unknown')}  
                    **Date**: {event.get('date', 'Unknown')}  
                    **Time**: {event.get('time', 'Unknown')}  
                    **Scale**: {event.get('scale', 'Unknown') or 'Not specified'}  
                    **Source**: {event.get('source', {}).get('source', {}).get('name', 'Unknown')}
                    """)
                    st.divider()
        else:
            st.info(f"No event details found in the saved data for {city}")

search_button = st.button("Search for Traffic Events", type="primary")

if search_button and city:
    with st.spinner(f"Searching for news in {city}..."):
        # Fetch news with city in the query
        query = f"{city} AND (traffic OR construction OR road OR concert OR event OR festival)"
        
        # Try to fetch real news, fallback to mock data if API key not available
        try:
            articles = fetch_news(query=query, days=days)
            if not articles:
                st.warning("No articles found or API key issue. Generating mock data...")
                articles = generate_mock_data_for_city(city, num_articles=10)
        except Exception as e:
            st.error(f"Error fetching news: {e}")
            st.info("Using mock data instead...")
            articles = generate_mock_data_for_city(city, num_articles=10)
    
    st.success(f"Found {len(articles)} news articles about {city}")
    
    # Display raw articles in an expander
    with st.expander("Raw News Articles"):
        for i, article in enumerate(articles, 1):
            st.subheader(f"Article #{i}: {article.get('title', 'No Title')}")
            st.write(f"Source: {article.get('source', {}).get('name', 'Unknown')}")
            st.write(f"Description: {article.get('description', 'No description')}")
            st.write("---")
    
    # Process with AI
    with st.spinner("Analyzing articles for traffic relevance..."):
        events = detect_events_by_city(articles, city)
    
    # Display results
    if events:
        st.success(f"Detected {len(events)} traffic-affecting events in {city}")
        
        # Save the events to city-specific file
        file_path = save_city_events(events, country_code, city)
        if file_path:
            st.info(f"Saved event data to {os.path.basename(file_path)}")
        
        # Convert to DataFrame for easier display
        events_list = []
        for event in events:
            event_dict = {
                "Type": event.get('event_type', 'Unknown'),
                "Location": event.get('location', 'Unknown'),
                "Date": event.get('date', 'Unknown'),
                "Time": event.get('time', 'Unknown'),
                "Scale": event.get('scale', 'Unknown'),
                "Source": event.get('source', {}).get('source', {}).get('name', 'Unknown')
            }
            events_list.append(event_dict)
        
        df = pd.DataFrame(events_list)
        st.dataframe(df, use_container_width=True)
        
        # Also display as cards for better visualization
        st.subheader("Events Detail View")
        cols = st.columns(3)
        
        for i, event in enumerate(events):
            with cols[i % 3]:
                st.markdown(f"""
                **Event Type**: {event.get('event_type', 'Unknown')}  
                **Location**: {event.get('location', 'Unknown')}  
                **Date**: {event.get('date', 'Unknown')}  
                **Time**: {event.get('time', 'Unknown')}  
                **Scale**: {event.get('scale', 'Unknown') or 'Not specified'}  
                **Source**: {event.get('source', {}).get('source', {}).get('name', 'Unknown')}
                """)
                st.divider()
    else:
        st.info(f"No traffic-affecting events detected in {city}")
else:
    if not city and search_button:
        st.warning("Please select or enter a city name to search for events")
    elif not search_button:
        st.info("Select a country and city, then click 'Search for Traffic Events' to begin") 