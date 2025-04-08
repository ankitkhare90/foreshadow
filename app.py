import re
import time
import os
from datetime import datetime, timedelta

import folium
import pandas as pd
import streamlit as st
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

from utils.data_storage import get_city_events, save_city_events
from utils.event_finder import find_traffic_events
from utils.geo_tagger import geo_tag_events
from utils.location_utils import get_cities_for_country, get_country_options
from utils.date_utils import parse_date, format_date

# Initialize session state for API key
if "openai_api_key" not in st.session_state:
    st.session_state.openai_api_key = ""

# Helper function to extract website name
def get_website_name(url):
    """Extract the website name from a URL"""
    if isinstance(url, str) and url.startswith('http'):
        match = re.search(r'https?://(?:www\.)?([^/]+)', url)
        if match:
            return match.group(1).split('.')[0]
    return url

# Helper function to create map with events
def create_event_map(events):
    """Create a folium map with events plotted as markers with popups and radius circles"""
    # Find events with coordinates
    events_with_coords = [e for e in events if e.get('latitude') and e.get('longitude')]
    
    if not events_with_coords:
        return None
    
    # Calculate center of map (average of all coordinates)
    avg_lat = sum(e.get('latitude', 0) for e in events_with_coords) / len(events_with_coords)
    avg_lng = sum(e.get('longitude', 0) for e in events_with_coords) / len(events_with_coords)
    
    # Create map centered on average coordinates
    m = folium.Map(location=[avg_lat, avg_lng], zoom_start=10, tiles="OpenStreetMap")
    
    # Add marker cluster group
    marker_cluster = MarkerCluster().add_to(m)
    
    # Define colors for different impact levels
    impact_colors = {
        'high': 'red',
        'medium': 'orange',
        'low': 'blue',
        'unknown': 'blue'
    }
    
    # Sort events by impact level (low→medium→high) so that smaller circles appear on top
    impact_order = {'low': 1, 'medium': 2, 'high': 3, 'unknown': 4}
    sorted_events = sorted(
        events_with_coords,
        key=lambda e: impact_order.get(e.get('traffic_impact', 'unknown').lower(), 5)
    )
    
    # Add markers and circles for each event
    for event in sorted_events:
        # Get event details
        lat, lng = event.get('latitude'), event.get('longitude')
        event_name = event.get('event_name') or "Unnamed Event"
        event_type = event.get('event_type', 'Unknown')
        location = event.get('location', 'Unknown')
        start_date = event.get('start_date', 'Unknown')
        end_date = event.get('end_date', 'Unknown')
        
        # Combine start and end time for display
        start_time = event.get('start_time', '')
        end_time = event.get('end_time', '')
        time_display = start_time
        if end_time and end_time != start_time:
            time_display = f"{start_time} - {end_time}"
            
        impact = event.get('traffic_impact', 'unknown').lower()
        
        # Set circle radius based on traffic impact (in meters)
        if impact == 'high':
            radius_m = 1000  # 1000 meters for high impact
            fill_opacity = 0.1  # Lower opacity for large circles
            weight = 1  # Thinner border
        elif impact == 'medium':
            radius_m = 500   # 500 meters for medium impact
            fill_opacity = 0.15
            weight = 2
        elif impact == 'low':
            radius_m = 250   # 250 meters for low impact
            fill_opacity = 0.2
            weight = 3  # Thicker border
        else:
            radius_m = 250   # Default to 250 meters for unknown impact
            fill_opacity = 0.2
            weight = 2
        
        # Get radius in km for display
        radius_km = radius_m / 1000
        
        # Create popup HTML
        popup_html = f"""
        <div style="width: 250px">
            <h5>{event_type.capitalize()}</h5>
            <b>Event Name:</b> {event_name}<br>
            <b>Location:</b> {location}<br>
            <b>Date:</b> {start_date} - {end_date}<br>
            <b>Time:</b> {time_display}<br>
            <b>Traffic Impact:</b> {impact.upper()}<br>
            <b>Impact Radius:</b> {radius_km} km<br>
        </div>
        """
        
        # Add marker with popup
        folium.Marker(
            location=[lat, lng],
            popup=folium.Popup(popup_html, max_width=300),
            icon=folium.Icon(color=impact_colors.get(impact, 'blue'))
        ).add_to(marker_cluster)
        
        # Create circle popup HTML with more information
        circle_popup_html = f"""
        <div style="width: 250px">
            <h5>{event_type.capitalize()}</h5>
            <b>Event Name:</b> {event_name}<br>
            <b>Location:</b> {location}<br>
            <b>Date:</b> {start_date} - {end_date}<br>
            <b>Time:</b> {time_display}<br>
            <b>Traffic Impact:</b> {impact.upper()}<br>
            <b>Impact Radius:</b> {radius_km} km<br>
        </div>
        """
        
        # Add circle to show impact radius
        folium.Circle(
            location=[lat, lng],
            radius=radius_m,
            color=impact_colors.get(impact, 'blue'),
            fill=True,
            fill_opacity=fill_opacity,
            weight=weight,
            popup=folium.Popup(circle_popup_html, max_width=250)
        ).add_to(m)
    
    return m

def show_event_table(events):
    """Create a table of events with columns for event type, name, location, date, time, and impact"""
    all_events = []
    for event in events:
        source_url = event.get('source', 'Unknown')
        website_name = get_website_name(source_url)
        
        # Get time information - combine start and end time
        start_time = event.get('start_time', '')
        end_time = event.get('end_time', '')
        time_display = start_time
        if end_time and end_time != start_time:
            time_display = f"{start_time} - {end_time}"
        
        event_display_item = {
            "Start Date": event.get('start_date', 'Unknown'),
            "End Date": event.get('end_date', 'Unknown'),
            "Type": event.get('event_type', 'Unknown'),
            "Name": event.get('event_name', '') or 'N/A',
            "Location": event.get('location', 'Unknown'),
            "Time": time_display,
            "Impact": event.get('traffic_impact', 'Unknown').upper(),
            "Url": source_url,  # Just use the raw URL
            "Website": website_name
        }
        
        # Add coordinates if available
        latitude = event.get("latitude")
        longitude = event.get("longitude")
        if latitude and longitude:
            event_display_item["Coordinates"] = f"{latitude:.4f}, {longitude:.4f}"
            
        all_events.append(event_display_item)
    
    if all_events:
        events_df = pd.DataFrame(all_events)
        st.dataframe(
            events_df,
            column_config={
                "Url": st.column_config.LinkColumn(
                    "Url",
                    display_text="🔗"
                )
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No events found")
        
def show_events_map(events, key_suffix="default"):
    col1, col2, col3 = st.columns([1, 10, 1])
    with col2:
        map_saved = create_event_map(events)
        if map_saved:
            # Use a unique key for each map instance
            map_key = f"map_{key_suffix}"
            st_folium(map_saved, width=800, height=600, returned_objects=[], key=map_key)
            
            # Add legend/explanation below map
            st.markdown("""
            <div style="padding: 10px; border-radius: 5px; font-size: 0.9em;">
                <p><strong>Map Legend:</strong></p>
                <ul style="margin: 0; padding-left: 20px;">
                    <li><span style="color: red; font-weight: bold;">Red markers</span>: High traffic impact</li>
                    <li><span style="color: orange; font-weight: bold;">Orange markers</span>: Medium traffic impact</li>
                    <li><span style="color: blue; font-weight: bold;">Blue markers</span>: Low or unknown traffic impact</li>
                    <li><span style="color: green; font-weight: bold;">Green circles with numbers</span>: Clusters of multiple markers - zoom in to expand</li>
                </ul>
                <p style="margin-top: 5px; font-style: italic; font-size: 0.85em;">Circles around markers indicate estimated impact radius. Click on markers or circles for event details.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("No geographic coordinates available for saved events.")

# ==============================================================================
# Section: Page Start
# ==============================================================================

st.set_page_config(
    page_title="Traffic Event Finder",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None
)

# Apply custom CSS to reduce top padding
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 4rem;
    }
</style>
""", unsafe_allow_html=True)

# Main title in the main area
st.title("🚦 Traffic Event Finder")

# Add controls to sidebar
with st.sidebar:
    st.header("Search Controls")
    openai_api_key = st.text_input(
        "Enter your OpenAI API Key:",
        type="password",
        value=st.session_state.openai_api_key,
        help="Your OpenAI API key is required for event search functionality. The key should start with 'sk-' and you can obtain it from your OpenAI account."
    )
    
    # Store API key in session state
    st.session_state.openai_api_key = openai_api_key
    
    # Replace standard divider with custom styled one
    st.markdown("""
    <hr style="margin: 0.5rem 0; padding: 0; height: 1px; border: none; background-color: rgba(49, 51, 63, 0.2);">
    """, unsafe_allow_html=True)
    
    # Country selection
    country_options = get_country_options()
    # Find index of India in the country options
    india_index = next((i for i, (code, _) in enumerate(country_options) if code == "IN"), 0)
    selected_country_code, selected_country_name = st.selectbox(
        "Select a country:",
        options=country_options,
        format_func=lambda x: x[1],  # Display country name
        index=india_index
    )

    # City selection based on country
    available_cities = get_cities_for_country(selected_country_code)
    if available_cities:
        # Find index of Mumbai in the available cities
        mumbai_index = next((i for i, city in enumerate(available_cities) if city == "Mumbai"), 0)
        selected_city = st.selectbox("Select a city:", options=available_cities, index=mumbai_index)
    else:
        selected_city = st.text_input("Enter a city name (no predefined cities available for this country):", placeholder="e.g., San Francisco")
    
    # Add search options - either days ahead or custom date range
    st.sidebar.subheader("Date Range Options")
    search_option = st.sidebar.radio("Search by:", ["Days ahead", "Custom date range"])
    
    today = datetime.now().date()
    
    if search_option == "Days ahead":
        search_days_ahead = st.sidebar.slider("Number of days to search ahead:", min_value=1, max_value=30, value=7)
        start_date = today
        end_date = today + timedelta(days=search_days_ahead)
        
        # Show selected range in readable format
        st.sidebar.info(f"Search period: {format_date(start_date)} to {format_date(end_date)}")
    else:
        col1, col2 = st.sidebar.columns(2)
        with col1:
            start_date = st.date_input(
                "From:",
                value=today,
                min_value=today,
                max_value=today + timedelta(days=365),
                key="start_date_select",
                help="Select start date for event search"
            )
        with col2:
            end_date = st.date_input(
                "To:",
                value=today + timedelta(days=7),
                min_value=start_date,
                max_value=today + timedelta(days=365),
                key="end_date_select",
                help="Select end date for event search"
            )

    # Check for existing events and add view option
    events = get_city_events(selected_country_code, selected_city, start_date=start_date, end_date=end_date)
    if events:
        st.info(f"Found {len(events)} previously saved events for {selected_city} within the selected date range.")
        show_saved_events = st.button("View Saved Events", type="secondary", use_container_width=True)
    else:
        show_saved_events = False
    
    # Add search button 
    search_button = st.button("Search for Traffic Events", type="primary", use_container_width=True)

# ==============================================================================
# Section: View Saved Events
# ==============================================================================

if show_saved_events and events:
    tab1, tab2 = st.tabs(["📈 Map", "🗃 Data"])
    with tab1:
        show_events_map(events, key_suffix="saved_events")
    with tab2:
        show_event_table(events)

# ==============================================================================
# Section: Search
# ==============================================================================

if search_button and selected_city:
    # Check if OpenAI API key is provided
    if not st.session_state.openai_api_key:
        st.error("Please enter your OpenAI API key in the sidebar to search for events.")
    else:
        with st.status(f"Searching for traffic events in {selected_city}...", expanded=True) as status:
            try:
                st.write("Finding traffic events...")
                event_types = ["concert/ live shows/ sport event", "road closure/ construction", "public protest/ demonstration/ gathering"]
                all_events = []
                for event_type in event_types:
                    events = find_traffic_events(selected_city, selected_country_code, start_date=start_date, end_date=end_date, event_type=event_type)
                    st.write(f"Found {len(events)} traffic-affecting events for {event_type} category.")
                    all_events.extend(events)
                
                if all_events:
                    st.write(f"Found {len(all_events)} traffic-affecting events")
                    
                    events_for_storage = []
                    for event in all_events:
                        storage_ready_event = {
                            'event_type': event.get('event_type', 'Unknown'),
                            'event_name': event.get('event_name', ''),
                            'location': event.get('location', 'Unknown'),
                            'start_date': event.get('start_date', 'Unknown'),
                            'end_date': event.get('end_date', 'Unknown'),
                            'start_time': event.get('start_time', ''),
                            'end_time': event.get('end_time', ''),
                            'time': f"{event.get('start_time', '')} - {event.get('end_time', '')}",
                            'traffic_impact': event.get('traffic_impact', 'Unknown'),
                            'source': event.get('source', 'Unknown'),
                            'city_name': selected_city,
                            'country_code': selected_country_code
                        }
                        events_for_storage.append(storage_ready_event)
                    
                    status.update(
                        label=f"Geo Tagging started for {len(events_for_storage)} events in {selected_city}",
                        state="running"
                    )
                    st.write("Adding geographic coordinates to events...")
                    old_length = len(events_for_storage)
                    geotagged_events = geo_tag_events(events_for_storage, selected_city, selected_country_code)
                    new_length = len(geotagged_events)
                    if old_length != new_length:
                        st.write(f"Filtered out {old_length - new_length} events that are too far from the city center")
                    else:
                        st.write(f"Added geographic coordinates to {len(geotagged_events)} events")
                    
                    status.update(
                        label=f"Saving events...",
                        state="running"
                    )
                    st.write("Saving events...")
                    saved_file_path = save_city_events(geotagged_events, selected_country_code, selected_city)
                    time.sleep(0.5)
                    st.write("Events saved successfully.")
                    time.sleep(1)
                    status.update(
                        label=f"Found and saved {len(geotagged_events)} traffic events for {selected_city} city.",
                        state="complete",
                        expanded=False
                    )
                    
                else:
                    date_range_text = f"between {start_date.strftime('%d-%m-%Y')} and {end_date.strftime('%d-%m-%Y')}"
                    status.update(
                        label=f"No new traffic events found in {selected_city} for the {date_range_text}",
                        state="complete"
                    )
            except Exception as e:
                status.update(label=f"Error finding traffic events: {e}", state="error")
                st.error(f"Error finding traffic events: {e}")

        # Display events after search
        events = get_city_events(selected_country_code, selected_city, start_date=start_date, end_date=end_date)
        if events:
            tab1, tab2 = st.tabs(["📈 Map", "🗃 Data"])
            with tab1:
                show_events_map(events, key_suffix="search_results")
            with tab2:
                show_event_table(events)

if not show_saved_events and not search_button:
    # Display instructions when no action has been taken
    st.info("👈 Use the sidebar to select a location and search options, then click 'Search for Traffic Events' to begin")
    
    # Optionally, add some helpful information about the app
    with st.expander("About this app"):
        st.markdown("""
        This app helps you find events that may affect traffic in your selected city.
        
        ### Core Components
        - Web Interface (Streamlit) for user interaction
        - Event Discovery using AI-powered web search (OpenAI API)
        - Geocoding System to convert locations to coordinates (Google Geocoding API)
        - Data Storage for caching discovered events
        - Visualization tools to display events on interactive maps

        ### Workflow
        - User selects location and date range parameters
        - System searches for traffic-impacting events (concerts, construction, protests, etc.)
        - Events are geocoded to obtain precise coordinates
        - Results are stored in JSON files to prevent duplicate searches
        - Events are displayed on an interactive map with color-coded impact indicators
        
        Use the sidebar controls to get started!
        """)
