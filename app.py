import os
import pandas as pd
import streamlit as st
import json
import re

from utils.data_storage import get_city_events, save_city_events
from utils.location_utils import get_cities_for_country, get_country_options
from utils.event_finder import find_traffic_events

# Helper function to extract website name
def get_website_name(url):
    if isinstance(url, str) and url.startswith('http'):
        match = re.search(r'https?://(?:www\.)?([^/]+)', url)
        if match:
            return match.group(1).split('.')[0]
    return url

st.set_page_config(
    page_title="Traffic Event Finder",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items=None
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

# Add a slider for the number of days to search
days = st.slider("Number of days to search ahead:", min_value=1, max_value=30, value=7)

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
            # Extract website name for display
            source_url = event.get('source', 'Unknown')
            website_name = get_website_name(source_url)
            
            event_dict = {
                "Type": event.get('event_type', 'Unknown'),
                "Name": event.get('event_name', '') or 'N/A',
                "Location": event.get('location', 'Unknown'),
                "Date": event.get('date', 'Unknown'),
                "Time": event.get('time', 'Unknown'),
                "Impact": event.get('traffic_impact', 'Unknown').upper(),
                "Source": source_url,
                "Website": website_name,
                "City": event.get('city_name', 'Unknown'),
            }
            events_list.append(event_dict)
        
        if events_list:
            df = pd.DataFrame(events_list)
            
            # Configure Source column as LinkColumn without lambda
            st.dataframe(
                df,
                column_config={
                    "Source": st.column_config.LinkColumn(
                        "Source",
                        help="Link to the source of the event information",
                        display_text="Website"
                    )
                },
                use_container_width=True
            )
        else:
            st.info(f"No event details found in the saved data for {city}")

search_button = st.button("Search for Traffic Events", type="primary")

if search_button and city:
    # Create a status container to track progress
    events = []  # Initialize events list outside the try block
    file_path = None  # Initialize file_path variable
    
    with st.status(f"Searching for traffic events in {city}...", expanded=True) as status:
        try:
            st.write("Finding traffic events...")
            events = find_traffic_events(city, country_code, days)
            
            if events:
                st.write(f"Found {len(events)} traffic-affecting events")
                
                st.write("Saving event data...")
                # Convert events from event_finder format to data_storage format
                storage_events = []
                for event in events:
                    storage_event = {
                        'event_type': event.get('event_type', 'Unknown'),
                        'event_name': event.get('event_name', ''),
                        'location': event.get('location', 'Unknown'),
                        'date': event.get('date', 'Unknown'),
                        'start_time': event.get('start_time', ''),
                        'end_time': event.get('end_time', ''),
                        'time': f"{event.get('start_time', '')} - {event.get('end_time', '')}",
                        'traffic_impact': event.get('traffic_impact', 'Unknown'),
                        'source': event.get('source', 'Unknown'),
                        'city_name': city,
                        'country_code': country_code
                    }
                    storage_events.append(storage_event)
                
                file_path = save_city_events(storage_events, country_code, city)
                
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
            status.update(label=f"Error finding traffic events: {e}", state="error")
            st.error(f"Error finding traffic events: {e}")
    
    # Display results
    if events:
        st.success(f"Found {len(events)} traffic-affecting events in {city}")
        
        if file_path:
            st.toast(f"Saved event data to {os.path.basename(file_path)}", icon="✅")
        
        # Display events in a table
        event_data = []
        for event in events:
            source_url = event.get("source", "Unknown")
            website_name = get_website_name(source_url)
            
            event_data.append({
                "Type": event.get("event_type", "Unknown"),
                "Name": event.get("event_name", "N/A") or "N/A",
                "Location": event.get("location", "Unknown"),
                "Date": event.get("date", "Unknown"),
                "Time": f"{event.get('start_time', '')} - {event.get('end_time', '')}",
                "Impact": event.get("traffic_impact", "Unknown").upper(),
                "Source": source_url,
                "Website": website_name
            })

        df_events = pd.DataFrame(event_data)
        
        # Use dataframe with LinkColumn for Source without lambda
        st.dataframe(
            df_events,
            column_config={
                "Source": st.column_config.LinkColumn(
                    "Source",
                    help="Link to the source of the event information",
                    display_text="Website"
                ),
                "Impact": st.column_config.TextColumn(
                    "Impact Level",
                    help="Estimated traffic impact"
                )
            },
            use_container_width=True
        )
        
        # Also show the raw JSON for reference
        with st.expander("View raw JSON data"):
            st.code(json.dumps(events, indent=2), language="json")
    else:
        st.info(f"No traffic-affecting events found for {city}")

else:
    if not city and search_button:
        st.warning("Please select or enter a city name to search for events")
    elif not search_button:
        st.info("Select a country and city, then click 'Search for Traffic Events' to begin")
