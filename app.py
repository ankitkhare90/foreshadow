import os

import pandas as pd
import streamlit as st

from utils.data_storage import get_city_events, save_city_events
from utils.event_detector import extract_event_from_article
from utils.location_utils import get_cities_for_country, get_country_options
from utils.news_fetcher import fetch_news

st.set_page_config(
    page_title="Foreshadow - Traffic Event Detector",
    page_icon="🚦",
    layout="wide"
)

st.title("🚦 Foreshadow: Traffic Event Detector")
st.subheader("Detect traffic-affecting events in your city")

# Main content area
# Country selection
country_options = get_country_options()
cols = st.columns(2)

with cols[0]:
    country_code, country_name = st.selectbox(
        "Select a country:",
        options=country_options,
        format_func=lambda x: x[1],  # Display country name
        index=0
    )

with cols[1]:
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
                "City": event.get('city_name', 'Unknown'),
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
                    **City**: {event.get('city_name', 'Unknown')}
                    """)
                    st.divider()
        else:
            st.info(f"No event details found in the saved data for {city}")

search_button = st.button("Search for Traffic Events", type="primary")

if search_button and city:
    with st.spinner(f"Searching for news in {city}..."):
        # Fetch news with city in the query
        query = f"{city}"
        
        # Try to fetch real news, fallback to mock data if API key not available
        try:
            articles = fetch_news(query=query, days=days)
            if not articles:
                st.warning("No articles found or API key issue.")
            else:
                st.success(f"Found {len(articles)} news articles about {city}")
        except Exception as e:
            st.error(f"Error fetching news: {e}")
    
    # Process with AI
    with st.spinner("Analyzing articles for traffic relevance..."):
        events = []
        for article in articles:
            event = extract_event_from_article(articles, city)
            events.append(event)
    
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
                "City": event.get('city_name', 'Unknown'),
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
                **City**: {event.get('city_name', 'Unknown')}
                """)
                st.divider()
    else:
        st.info(f"No traffic-affecting events detected in {city}")
else:
    if not city and search_button:
        st.warning("Please select or enter a city name to search for events")
    elif not search_button:
        st.info("Select a country and city, then click 'Search for Traffic Events' to begin") 