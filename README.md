# Foreshadow: Traffic Event Detector

Foreshadow is a city-based traffic event detection system that leverages news articles and AI to identify traffic-affecting events. This project follows a functional programming approach with modular components.

## Features

- **City-based filtering**: Search for traffic events in specific cities
- **Two-phase AI analysis**:
  1. First filters news articles for traffic relevance
  2. Then extracts structured event data from relevant articles
- **Structured event data**:
  - Event type (concert, sports, construction, etc.)
  - Location (specific as possible)
  - Date and time
  - Scale/attendance (when available)
- **Geographic tagging**: Adds coordinates and influence radius to events
- **Data persistence**: Save and retrieve events
- **Streamlit user interface**: Easy interactive exploration

## Installation

1. Clone this repository
2. Install dependencies:
   ```
   uv pip install -r requirements.txt
   ```
3. Set up environment variables in a `.env` file:
   ```
   OPENAI_API_KEY=your_openai_api_key
   NEWSAPI_API_KEY=your_newsapi_key
   ```

## Usage

### Run the Streamlit app:

```bash
streamlit run app.py
```

### Run the command-line demo:

Basic version (without geolocation):
```bash
python example_usage.py
```

Full pipeline version (with geolocation and storage):
```bash
python full_pipeline_example.py
```

## Components

The project uses a functional approach with these modules:

- **event_detector.py**: Functions for detecting traffic-affecting events
  - `detect_events_by_city`: Main function to process articles by city
  - `is_traffic_relevant`: Checks if articles are traffic-relevant
  - `extract_events_with_llm`: Extracts structured event data
  
- **news_fetcher.py**: Functions for retrieving news
  - `fetch_news`: Gets news from an external API
  - `generate_mock_data`: Creates test data when API unavailable

- **geo_tagger.py**: Functions for adding geographic coordinates
  - `geo_tag_events`: Main function to add location coordinates
  - `disambiguate_location`: Enhances location references
  - `calculate_influence_radius`: Determines traffic impact radius

- **data_storage.py**: Functions for data persistence
  - `save_events`: Stores events with timestamps
  - `get_events`: Retrieves events with optional date filtering

## How It Works

1. **News Fetching**: Gets news related to the specified city
2. **Traffic Relevance Check**: Uses AI to filter for traffic-related articles
3. **Event Extraction**: Analyzes relevant articles to extract structured event data
4. **Geographic Tagging**: Enhances events with coordinates and influence radius
5. **Storage**: Persists events for future retrieval
6. **Display**: Shows events in an easily digestible format

## API Keys

- OpenAI API key: Required for AI analysis
- NewsAPI key: Required for fetching real news articles

If keys are missing, the system falls back to mock data generation for demonstration purposes.

## Requirements

```
streamlit
pandas
openai
requests
python-dotenv
geopy
```

# Country Cities Generator

This script generates separate JSON files for each country, with each file containing all cities for that country. It uses the `worldcities.csv` dataset as input.

## Requirements

Before running the script, install the required dependencies:

```bash
uv pip install pandas
```

## Usage

1. Make sure `worldcities.csv` is in the root directory of the project
2. Run the script with:

```bash
python generate_country_city_files.py
```

## Output

The script creates a directory named `data/prefill_city_data` that contains JSON files for each country, with filenames based on the country's 2-letter code (e.g., `US.json`, `GB.json`, `IN.json`).

Each JSON file contains a direct array of city names:

```json
[
  "City1",
  "City2",
  ...
]
```

## Input Data Format

The script expects the `worldcities.csv` file to have at least these columns:
- `city`: City name
- `iso2`: Two-letter country code (ISO 3166-1 alpha-2)