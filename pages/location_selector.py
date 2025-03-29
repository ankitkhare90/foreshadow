import streamlit as st
from utils.location_utils import get_country_options, get_cities_for_country

def main():
    st.title("Country and City Selector")
    
    # Get country options
    country_options = get_country_options()
    country_names = [name for _, name in country_options]
    country_codes = [code for code, _ in country_options]
    
    # Create a selectbox for country selection
    selected_country_idx = st.selectbox(
        "Select a country",
        range(len(country_names)),
        format_func=lambda i: country_names[i]
    )
    
    selected_country_code = country_codes[selected_country_idx]
    selected_country_name = country_names[selected_country_idx]
    
    st.write(f"Selected country: {selected_country_name} ({selected_country_code})")
    
    # Get cities for the selected country
    cities = get_cities_for_country(selected_country_code)
    
    # Create a selectbox for city selection if cities are available
    if cities:
        selected_city = st.selectbox("Select a city", cities)
        st.write(f"Selected city: {selected_city}")
    else:
        st.warning(f"No cities available for {selected_country_name}")
    
    # Display some stats
    st.subheader("Country Statistics")
    st.write(f"Number of countries available: {len(country_options)}")
    st.write(f"Number of cities available for {selected_country_name}: {len(cities)}")

if __name__ == "__main__":
    main() 