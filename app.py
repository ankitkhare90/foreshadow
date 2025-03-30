import os
import pandas as pd
import streamlit as st
import json
import re
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster

from utils.data_storage import get_city_events, save_city_events
from utils.location_utils import get_cities_for_country, get_country_options
from utils.event_finder import find_traffic_events
from utils.geo_tagger import geo_tag_events

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
    m = folium.Map(location=[avg_lat, avg_lng], zoom_start=12, tiles="OpenStreetMap")
    
    # Add marker cluster group
    marker_cluster = MarkerCluster().add_to(m)
    
    # Define colors for different impact levels
    impact_colors = {
        'high': 'red',
        'medium': 'orange',
        'low': 'green',
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
        time = event.get('time', '')
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
            <b>Time:</b> {time}<br>
            <b>Traffic Impact:</b> {impact.upper()}<br>
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
            <b>Time:</b> {time}<br>
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
        
        event_display_item = {
            "Start Date": event.get('start_date', 'Unknown'),
            "End Date": event.get('end_date', 'Unknown'),
            "Type": event.get('event_type', 'Unknown'),
            "Name": event.get('event_name', '') or 'N/A',
            "Location": event.get('location', 'Unknown'),
            "Time": event.get('time', 'Unknown'),
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
        
        # Sort dataframe by date (earliest first)
        try:
            # Try converting to datetime for proper sorting
            events_df['Start Date'] = pd.to_datetime(events_df['Start Date'], errors='coerce')
            events_df['End Date'] = pd.to_datetime(events_df['End Date'], errors='coerce')
            events_df = events_df.sort_values('Start Date')
            # Format dates back to string for display
            events_df['Start Date'] = events_df['Start Date'].dt.strftime('%d-%m-%Y')
            events_df['End Date'] = events_df['End Date'].dt.strftime('%d-%m-%Y')
        except Exception:
            # If date conversion fails, try basic string sorting
            events_df = events_df.sort_values('Start Date')
            
        # Place dataframe inside an expander
        with st.expander("Click to view event data table"):
            # Configure columns with proper formatting  
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
        
def show_events_map(events):
    col1, col2, col3 = st.columns([1, 10, 1])
    with col2:
        map_saved = create_event_map(events)
        if map_saved:
            st_folium(map_saved, width=800, height=600, returned_objects=[])
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

# Main title in the main area
st.title("🚦 Traffic Event Finder")
st.subheader("Find events that may affect traffic in your city")

# Add controls to sidebar
with st.sidebar:
    st.title("Search Controls")
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
    search_option = st.radio("Search by:", ["Days ahead", "Custom date range"])

    if search_option == "Days ahead":
        search_days_ahead = st.slider("Number of days to search ahead:", min_value=1, max_value=30, value=7)
        search_start_date = pd.Timestamp.now().date()
        search_end_date = pd.Timestamp.now().date() + pd.Timedelta(days=search_days_ahead)
    else:
        search_days_ahead = None
        search_start_date = st.date_input("Start date", format="DD-MM-YYYY")
        search_end_date = st.date_input("End date", format="DD-MM-YYYY")

    # Check for existing events and add view option
    events = get_city_events(selected_country_code, selected_city, start_date=search_start_date, end_date=search_end_date)
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
    show_event_table(events)
    st.subheader(f"Map of Events in {selected_city}")
    show_events_map(events)

# ==============================================================================
# Section: Search
# ==============================================================================

if search_button and selected_city:
    
    with st.status(f"Searching for traffic events in {selected_city}...", expanded=True) as status:
        try:
            st.write("Finding traffic events...")

            events = find_traffic_events(selected_city, selected_country_code, start_date=search_start_date, end_date=search_end_date)
            date_range_text = f"between {search_start_date.strftime('%d-%m-%Y')} and {search_end_date.strftime('%d-%m-%Y')}"
            
            if events:
                st.write(f"Found {len(events)} traffic-affecting events")
                
                events_for_storage = []
                for event in events:
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
                    
                st.write("Adding geographic coordinates to events...")
                geotagged_events = geo_tag_events(events_for_storage)
                st.write("Saving events to file...")
                saved_file_path = save_city_events(geotagged_events, selected_country_code, selected_city)
                st.write("Events saved to file...")
                status.update(
                    label=f"Found {len(events)} traffic events in {selected_city}",
                    state="complete"
                )
                
            else:
                status.update(
                    label=f"No new traffic events found in {selected_city} for the {date_range_text}",
                    state="complete"
                )
        except Exception as e:
            status.update(label=f"Error finding traffic events: {e}", state="error")
            st.error(f"Error finding traffic events: {e}")

    events = get_city_events(selected_country_code, selected_city, start_date=search_start_date, end_date=search_end_date)
    show_event_table(events)
    show_events_map(events)

elif not show_saved_events:
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
        - Visualize events on an interactive map with impact radius
        
        Use the sidebar controls to get started!
        """)
