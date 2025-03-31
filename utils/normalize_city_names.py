import json
import os
import unicodedata
import glob

def normalize_string(s):
    """
    Normalize a string by replacing non-ASCII characters with their ASCII equivalents.
    For example, "Hyderābād" becomes "Hyderabad"
    """
    # Normalize to NFD form to separate base characters from diacritical marks
    normalized = unicodedata.normalize('NFD', s)
    # Remove diacritical marks and keep only ASCII characters
    ascii_string = ''.join(c for c in normalized if not unicodedata.combining(c))
    return ascii_string

def normalize_city_names(country_code=None):
    """
    Normalize city names in JSON files.
    If country_code is provided, only normalize that country's file.
    Otherwise, normalize all country files.
    """
    base_path = os.path.join('data', 'prefill_city_data')
    
    if country_code:
        # Normalize a specific country file
        file_path = os.path.join(base_path, f"{country_code}.json")
        if os.path.exists(file_path):
            normalize_file(file_path)
            print(f"Normalized city names for {country_code}")
        else:
            print(f"File not found: {file_path}")
    else:
        # Normalize all country files
        pattern = os.path.join(base_path, "*.json")
        for file_path in glob.glob(pattern):
            normalize_file(file_path)
            country_code = os.path.basename(file_path).split('.')[0]
            print(f"Normalized city names for {country_code}")

def normalize_file(file_path):
    """
    Normalize city names in a single JSON file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            cities = json.load(f)
        
        # Normalize each city name
        normalized_cities = [normalize_string(city) for city in cities]
        
        # Write the normalized cities back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(normalized_cities, f, indent=2, ensure_ascii=True)
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Normalize a specific country file
        normalize_city_names(sys.argv[1])
    else:
        # Normalize all country files
        normalize_city_names() 