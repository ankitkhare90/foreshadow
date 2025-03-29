import streamlit as st
import json
from utils.news_fetcher import fetch_news, generate_mock_data_for_city
from utils.event_detector import detect_events_by_city
import pandas as pd

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
    1. Enter a city name
    2. The app searches for news about that city
    3. AI identifies which news could affect traffic
    4. For relevant news, AI extracts structured event details
    """)

# Main content area
city = st.text_input("Enter a city name:", placeholder="e.g., San Francisco")

days = st.slider("Days of news to search:", min_value=1, max_value=30, value=7)

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
        st.warning("Please enter a city name to search for events")
    elif not search_button:
        st.info("Enter a city name and click 'Search for Traffic Events' to begin") 