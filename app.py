import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
from datetime import datetime, timedelta

from utils.news_fetcher import NewsFetcher
from utils.event_detector import EventDetector
from utils.geo_tagger import GeoTagger
from utils.data_storage import DataStorage

st.set_page_config(
    page_title="Traffic Prediction Tool",
    page_icon="🚦",
    layout="wide",
)

@st.cache_resource
def load_data_manager():
    data_storage = DataStorage()
    return data_storage

def run_pipeline(days=7, query="traffic OR construction OR road OR concert OR event", use_cached=True):
    data_storage = load_data_manager()
    
    # Check if we have data and should use cache
    events = data_storage.get_events()
    if events and use_cached:
        return events
    
    # Otherwise run the full pipeline
    news_fetcher = NewsFetcher()
    event_detector = EventDetector()
    geo_tagger = GeoTagger()
    
    articles = news_fetcher.fetch_news(query=query, days=days)
    if not articles:
        # Fall back to mock data for testing if no articles
        articles = news_fetcher.generate_mock_data(10)
    
    events = event_detector.detect_events(articles)
    geo_tagged_events = geo_tagger.geo_tag_events(events)
    data_storage.save_events(geo_tagged_events)
    
    return data_storage.get_events()

def create_map(events, default_location=(37.7749, -122.4194)):
    # Create a map centered on default location
    m = folium.Map(location=default_location, zoom_start=12)
    
    # Add event markers
    for event in events:
        if "coordinates" in event and event["coordinates"]:
            lat, lon = event["coordinates"]
            
            # Create popup content
            popup_content = f"""
            <b>{event.get('event_type', 'Event')}</b><br>
            Location: {event.get('location', 'Unknown')}<br>
            Date: {event.get('date', 'Unknown')}<br>
            """
            if "scale" in event and event["scale"]:
                popup_content += f"Scale: {event['scale']}<br>"
            
            # Determine color based on event type
            color = "blue"
            event_type = event.get("event_type", "").lower()
            if "concert" in event_type or "festival" in event_type:
                color = "green"
            elif "closure" in event_type or "construction" in event_type:
                color = "red"
            elif "accident" in event_type:
                color = "orange"
            
            # Add the marker
            folium.Marker(
                [lat, lon],
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=event.get('event_type', 'Event'),
                icon=folium.Icon(color=color),
            ).add_to(m)
            
            # Add circle showing influence radius
            if "influence_radius" in event and event["influence_radius"]:
                folium.Circle(
                    [lat, lon],
                    radius=event["influence_radius"] * 1000,  # Convert km to meters
                    color=color,
                    fill=True,
                    fill_opacity=0.1,
                ).add_to(m)
    
    return m

def main():
    st.title("🚦 Traffic Prediction Tool")
    st.markdown("### Based on News Event Detection")
    
    # Sidebar for controls
    with st.sidebar:
        st.header("Controls")
        
        # Data selection
        st.subheader("Data Source")
        use_cached = st.checkbox("Use cached data", value=True)
        days = st.slider("Days to look back", 1, 30, 7)
        query = st.text_input("Search query", "traffic OR construction OR road OR concert OR event")
        
        if st.button("Fetch New Data"):
            with st.spinner("Fetching and processing data..."):
                events = run_pipeline(days=days, query=query, use_cached=False)
                st.success(f"Found {len(events)} events")
    
    # Main content area
    st.subheader("Event Map")
    
    # Load events
    events = run_pipeline(days=days, query=query, use_cached=use_cached)
    
    # Display map
    if events:
        st.write(f"Displaying {len(events)} events")
        
        # Filter to only events with coordinates
        mapped_events = [e for e in events if "coordinates" in e and e["coordinates"]]
        
        if mapped_events:
            m = create_map(mapped_events)
            st_folium(m, width=1000, height=600)
        else:
            st.warning("No events with valid coordinates to display on map")
        
        # Display events table
        st.subheader("Event Details")
        
        # Prepare data for display
        display_data = []
        for event in events:
            display_data.append({
                "Type": event.get("event_type", "Unknown"),
                "Location": event.get("location", "Unknown"),
                "Date": event.get("date", "Unknown"),
                "Scale": event.get("scale", "")
            })
        
        # Display as table
        df = pd.DataFrame(display_data)
        st.dataframe(df)
    else:
        st.warning("No events found. Try adjusting search parameters.")
        
if __name__ == "__main__":
    main() 