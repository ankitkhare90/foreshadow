import os
import pandas as pd
import streamlit as st
import json

from utils.data_storage import get_city_events, save_city_events
from utils.event_detector import extract_event_from_article
from utils.location_utils import get_cities_for_country, get_country_options
from utils.news_fetcher import fetch_news
from utils.event_finder import find_traffic_events, generate_mock_events

st.set_page_config(
    page_title="Traffic Event Finder",
    page_icon="🚦",
    layout="wide"
)

st.title("🚦 Traffic Event Finder")
st.subheader("Find events that may affect traffic in your city")

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

# Add pagination controls
st.subheader("Search Settings")
articles_per_page = 100
max_pages = st.slider(f"Maximum pages to fetch ({articles_per_page} articles per page):", min_value=1, max_value=10, value=3)

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
        else:
            st.info(f"No event details found in the saved data for {city}")

search_button = st.button("Search for Traffic Events", type="primary")

if search_button and city:
    # Create a status container to track progress
    events = []  # Initialize events list outside the try block
    file_path = None  # Initialize file_path variable
    
    with st.status(f"Searching for traffic events in {city}...", expanded=True) as status:
        # Fetch news with city in the query
        st.write("Fetching news articles...")
        query = f"{city}"
        
        # Try to fetch real news
        try:
            all_articles = []
            total_results = 0
            
            # Fetch first page and get total count
            articles, total_results = fetch_news(query=query, days=days, page=1)
            all_articles.extend(articles)
            
            # Fetch additional pages if needed
            for page in range(2, min(max_pages + 1, (total_results // articles_per_page) + 2)):
                st.write(f"Fetching page {page} of articles...")
                more_articles, _ = fetch_news(query=query, days=days, page=page)
                if more_articles:
                    all_articles.extend(more_articles)
                else:
                    break
            
            if not all_articles:
                status.update(label="No articles found or API key issue", state="error")
                st.warning("No articles found or API key issue.")
            else:
                st.write(f"Found {len(all_articles)} news articles about {city} (out of {total_results} total results)")
                
                # Process with AI - Sequential approach to avoid multiprocessing issues
                st.write("Analyzing articles for traffic relevance...")
                for i, article in enumerate(all_articles):
                    progress = ((i + 1) / len(all_articles)) * 100
                    
                    # Update status message
                    if progress % 25 == 0:
                        st.write(f"{progress}% articles processed")
                    
                    # Process article
                    event = extract_event_from_article(article, city)
                    if event:
                        events.append(event)
                
                if events:
                    st.write(f"Detected {len(events)} traffic-affecting events")
                    
                    st.write("Saving event data...")
                    print("--------------------------------")
                    print(f"events: {events}")
                    print("--------------------------------")
                    file_path = save_city_events(events, country_code, city)
                    
                    status.update(
                        label=f"Found {len(events)} traffic events in {city}",
                        state="complete"
                    )
                else:
                    status.update(
                        label=f"No traffic events found in {city}",
                        state="complete"
                    )
        except Exception as e:
            status.update(label=f"Error fetching news: {e}", state="error")
            st.error(f"Error fetching news: {e}")
    
    # Display results
    if events:
        st.success(f"Detected {len(events)} traffic-affecting events in {city}")
        
        if file_path:
            st.toast(f"Saved event data to {os.path.basename(file_path)}", icon="✅")
        
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
    else:
        st.info(f"No traffic-affecting events detected in {city}")

else:
    if not city and search_button:
        st.warning("Please select or enter a city name to search for events")
    elif not search_button:
        st.info("Select a country and city, then click 'Search for Traffic Events' to begin")

# City input
city = st.text_input("Enter city name:", value="San Francisco")

# Choose between real search and mock data
use_mock = st.checkbox("Use mock data (for testing without API calls)", value=True)

if st.button("Find Events"):
    with st.spinner(f"Finding traffic events in {city}..."):
        if use_mock:
            events = generate_mock_events(city)
            st.info("Using mock data for demonstration purposes")
        else:
            events = find_traffic_events(city)
    
    if events:
        st.success(f"Found {len(events)} traffic events in {city}")
        
        # Display events in a table
        event_data = []
        for event in events:
            event_data.append({
                "Type": event["event_type"],
                "Name": event["event_name"] or "N/A",
                "Location": event["location"],
                "Date": event["date"],
                "Time": f"{event['start_time']} - {event['end_time']}",
                "Impact": event["traffic_impact"].upper(),
                "Source": event["source"]
            })
        
        st.table(event_data)
        
        # Also show the raw JSON for reference
        with st.expander("View raw JSON data"):
            st.code(json.dumps(events, indent=2), language="json")
    else:
        st.warning(f"No traffic events found for {city}")
        
st.markdown("---")
st.markdown("""
### How it works
This application uses OpenAI's GPT-4o model with web search capability to find real-time traffic events in cities.
The model searches the web for information about events that could affect traffic, such as:
- Concerts and festivals
- Sports events
- Road closures
- Construction
- Marathons and parades

For each event, it extracts structured information including location, date, times, and expected traffic impact.
""") 