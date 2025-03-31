# Foreshadow: Traffic Event Finder

A Streamlit application that helps users find and visualize upcoming events that may impact traffic in cities around the world.

## Features

- **Event Search**: Find events like concerts, sports, construction, festivals, and protests
- **Geographic Visualization**: View events on an interactive map with color-coded impact levels
- **Date Range Filtering**: Search for events by specific date ranges or days ahead
- **Multiple Cities**: Supports cities worldwide with country-specific presets
- **Impact Assessment**: Events are categorized by traffic impact (low, medium, high)
- **Detailed Information**: View complete event details including venue, date, time, and source

## Installation

### Setup

1. Clone the repository:
```bash
git clone https://github.com/ankit-ds/foreshadow.git
cd foreshadow
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the project root with the following variables:
```
OPENAI_API_KEY=your_openai_api_key
GEOCODE_USERNAME=mara/personnel/yourusername
GEOCODE_PWD=your_geocode_password
```

## Usage

1. Start the Streamlit application:
```bash
streamlit run app.py
```

2. In the app:
   - Select a country and city from the sidebar
   - Choose between searching by days ahead or a custom date range
   - Click "Find Events" to search for traffic events
   - View events on the interactive map and in the table
   - Filter events by type (concerts, construction, etc.)

## Data Flow

1. User selects location and date parameters
2. Application searches for events using OpenAI's API with web search capability
3. Events are geocoded to obtain latitude/longitude coordinates
4. Results are stored locally for future reference
5. Events are displayed on an interactive map and in a filterable table

## Structure

- **app.py**: Main Streamlit application
- **utils/**:
  - **data_storage.py**: Functions for saving and retrieving event data
  - **event_finder.py**: Functions for finding traffic events using OpenAI
  - **geo_tagger.py**: Functions for adding geographic coordinates to events
  - **location_utils.py**: Utilities for working with cities and countries
