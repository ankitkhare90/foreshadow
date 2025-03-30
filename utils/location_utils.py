import json
import os

from config.constants import CODE_COUNTRY


def get_country_options():
    """
    Returns a list of tuples with country codes and names for the dropdown.
    The list is sorted by country name.
    """
    return sorted([(code, name) for code, name in CODE_COUNTRY.items()], key=lambda x: x[1])

def get_cities_for_country(country_code):
    """
    Returns a list of cities for the given country code.
    If the country file doesn't exist or can't be read, returns an empty list.
    """
    file_path = os.path.join('data', 'prefill_city_data', f"{country_code}.json")
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            print(f"City file not found for country code: {country_code}")
            return []
    except Exception as e:
        print(f"Error reading city data for {country_code}: {e}")
        return [] 