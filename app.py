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
    initial_sidebar_state="expanded",
    menu_items=None
)

# Main title in the main area
st.title("🚦 Traffic Event Finder")
st.subheader("Find events that may affect traffic in your city")

# Add controls to sidebar
with st.sidebar:
    st.title("Search Controls")
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
    
    # Add search options - either days ahead or custom date range
    search_option = st.radio("Search by:", ["Days ahead", "Custom date range"])

    if search_option == "Days ahead":
        days = st.slider("Number of days to search ahead:", min_value=1, max_value=30, value=7)
        start_date = None
        end_date = None
    else:
        days = None
        start_date = st.date_input("Start date")
        end_date = st.date_input("End date", value=pd.Timestamp.now().date() + pd.Timedelta(days=7))

    # Check for existing events and add view option
    existing_events = get_city_events(country_code, city)
    if existing_events:
        st.info(f"Found {len(existing_events)} previously saved events for {city}.")
        view_saved = st.button("View Saved Events", type="secondary", use_container_width=True)
    else:
        view_saved = False
    
    # Add search button 
    search_button = st.button("Search for Traffic Events", type="primary", use_container_width=True)

# Main content area
if view_saved and existing_events:
    # Display saved events
    st.subheader(f"Saved Events for {city}")
    
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

if search_button and city:
    # Create a status container to track progress
    events = []  # Initialize events list outside the try block
    file_path = None  # Initialize file_path variable
    
    with st.status(f"Searching for traffic events in {city}...", expanded=True) as status:
        try:
            st.write("Finding traffic events...")
            
            # Use either days or date range based on the search option
            if search_option == "Days ahead":
                events = find_traffic_events(city, country_code, days=days)
                date_range_text = f"next {days} days"
            else:
                events = find_traffic_events(city, country_code, days=None, start_date=start_date, end_date=end_date)
                date_range_text = f"between {start_date.strftime('%d-%m-%Y')} and {end_date.strftime('%d-%m-%Y')}"
            
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
                    label=f"No traffic events found in {city} for the {date_range_text}",
                    state="complete"
                )
        except Exception as e:
            status.update(label=f"Error finding traffic events: {e}", state="error")
            st.error(f"Error finding traffic events: {e}")
    
    # Display results
    if events:
        st.subheader(f"Traffic Events in {city}")
        st.success(f"Found {len(events)} traffic-affecting events in {city} for the {date_range_text}")
        
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

elif not view_saved:
    # Display instructions when no action has been taken
    st.info("👈 Use the sidebar to select a location and search options, then click 'Search for Traffic Events' to begin")
    
    # Optionally, add some helpful information about the app
    with st.expander("About this app"):
        st.markdown("""
        This app helps you find events that may affect traffic in your selected city.
        
        ### Features:
        - Search for traffic events in cities worldwide
        - View events for a specific time period
        - Save search results for future reference
        - View detailed event information including location, date, and traffic impact
        
        Use the sidebar controls to get started!
        """)
