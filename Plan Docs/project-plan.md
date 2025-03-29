# Traffic Prediction Tool Based on News Event Detection

## Project Overview

This project aims to develop a predictive system that correlates news events with traffic patterns to forecast congestion in specific areas. The system will ingest news data, detect relevant events, map them to geographic locations, predict traffic impacts, and visualize these predictions through an interactive Streamlit interface.

## Technology Stack

- **Frontend**: Streamlit for interactive UI
- **Backend**: Python
- **NLP Engine**: OpenAI LLM API
- **Geocoding**: GeoPy
- **Maps Visualization**: Folium
- **Data Storage**: Pandas (for prototype), SQLite/PostgreSQL (for production)

## System Architecture

1. **News Ingestion and Event Detection Module**: Collects news data and uses OpenAI LLM to identify and classify events with potential traffic impact.
2. **Geo-tagging and Location Mapping Module**: Maps events to geographic coordinates using LLM for disambiguation.
3. **Traffic Prediction Engine**: Correlates geo-tagged events with traffic patterns to generate predictions.
4. **Visualization and User Interface**: Provides an interactive map-based interface with date selection.

## Implementation Roadmap

### Phase 1: Data Pipeline Setup (Week 1)
- Set up project environment and repository
- Implement news data collection from APIs
- Create LLM-powered event detection system
- Develop geo-tagging module
- Build basic data storage system

### Phase 2: Traffic Prediction Engine (Week 2)
- Implement grid system for geographic areas
- Create traffic impact scoring using LLM
- Develop prediction algorithm
- Build validation framework

### Phase 3: User Interface Development (Week 3)
- Create Streamlit app with basic layout
- Implement interactive map visualization
- Add date selection and filtering capabilities
- Develop event markers and popups

### Phase 4: Testing and Optimization (Week 4)
- Conduct systematic testing
- Optimize performance
- Refine UI/UX
- Deploy application

## Detailed Phase 1 Implementation: Data Pipeline Setup

### 1. Project Environment Setup (Day 1)

#### Tasks:
- Create GitHub repository for version control
- Set up Python virtual environment
- Install required libraries:
  ```
  uv pip install streamlit folium pandas openai geopy requests python-dotenv
  ```
- Create project structure:
  ```
  .
  ├── README.md
  ├── .env
  ├── app.py
  ├── data/
  ├── utils/
  │   ├── __init__.py
  │   ├── news_fetcher.py
  │   ├── event_detector.py
  │   ├── geo_tagger.py
  │   └── data_storage.py
  └── tests/
  ```

### 2. News Data Collection (Day 2)

#### Tasks:
- Create `utils/news_fetcher.py` to fetch news from sources
- Implement NewsAPI integration for real-time news
- Add option for mock data generation for testing
- Create caching mechanism to reduce API calls

#### Sample Implementation:
```python
import requests
import os
from dotenv import load_dotenv

load_dotenv()

class NewsFetcher:
    def __init__(self):
        self.api_key = os.getenv("NEWS_API_KEY")
        self.base_url = "https://newsapi.org/v2/everything"
    
    def fetch_news(self, query="traffic OR construction OR road OR concert OR event", days=7):
        params = {
            "q": query,
            "apiKey": self.api_key,
            "language": "en",
            "sortBy": "publishedAt",
            "from": (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        }
        response = requests.get(self.base_url, params=params)
        if response.status_code == 200:
            return response.json()["articles"]
        else:
            print(f"Error fetching news: {response.status_code}")
            return []
    
    def generate_mock_data(self, num_articles=10):
        # Generate mock articles for testing
        mock_events = [
            {"type": "concert", "location": "San Francisco", "date": "next Saturday"},
            {"type": "road closure", "location": "Downtown", "date": "tomorrow"},
            {"type": "construction", "location": "Highway 101", "date": "next week"},
            # Add more mock events
        ]
        
        articles = []
        for i in range(num_articles):
            event = random.choice(mock_events)
            articles.append({
                "title": f"{event['type'].title()} in {event['location']}",
                "description": f"A {event['type']} is scheduled in {event['location']} {event['date']}.",
                "publishedAt": datetime.now().isoformat(),
                "source": {"name": "Mock News"}
            })
        return articles
```

### 3. Event Detection with OpenAI LLM (Day 3-4)

#### Tasks:
- Create `utils/event_detector.py` for event extraction
- Implement OpenAI API integration
- Design prompt for event detection
- Extract event type, location, date and other relevant information

#### Sample Implementation:
```python
import openai
import os
from dotenv import load_dotenv

load_dotenv()

class EventDetector:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
    
    def detect_events(self, articles):
        events = []
        for article in articles:
            content = f"{article['title']}. {article['description']}"
            events_from_article = self._extract_events_with_llm(content)
            for event in events_from_article:
                event["source"] = article
            events.extend(events_from_article)
        return events
    
    def _extract_events_with_llm(self, text):
        prompt = f"""
        Extract traffic-related events from this text. For each event, provide:
        1. Event type (concert, road closure, construction, festival, etc.)
        2. Location (as specific as possible)
        3. Date and time (if available)
        4. Expected attendance or scale (if mentioned)
        
        Return JSON format only, with no explanation:
        [
          {{
            "event_type": "...",
            "location": "...",
            "date": "...",
            "scale": "..."
          }}
        ]
        
        If no traffic-related events are found, return an empty array.
        
        Text: {text}
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=500
        )
        
        try:
            return json.loads(response.choices[0].message['content'])
        except json.JSONDecodeError:
            print("Error parsing JSON response from LLM")
            return []
```

### 4. Geo-tagging Module (Day 5)

#### Tasks:
- Create `utils/geo_tagger.py` for location mapping
- Implement geocoding with GeoPy
- Add LLM-powered location disambiguation
- Calculate influence zones for events

#### Sample Implementation:
```python
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
import openai
import os
from dotenv import load_dotenv

load_dotenv()

class GeoTagger:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="traffic_predictor")
        openai.api_key = os.getenv("OPENAI_API_KEY")
    
    def geo_tag_events(self, events, city="San Francisco"):
        for event in events:
            if "location" in event and event["location"]:
                # Use LLM to disambiguate location if needed
                full_location = self._disambiguate_location(event["location"], city)
                coordinates = self._geocode_location(full_location)
                event["coordinates"] = coordinates
                
                # Calculate influence zone based on event type
                event["influence_radius"] = self._calculate_influence_radius(event)
        
        return events
    
    def _disambiguate_location(self, location, city):
        if city.lower() in location.lower():
            return location
            
        prompt = f"""
        Disambiguate this location reference: "{location}" within the city of {city}.
        Return only the full, specific location that would be recognized by a mapping service.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=100
        )
        
        return response.choices[0].message['content'].strip()
    
    def _geocode_location(self, location):
        try:
            location_data = self.geolocator.geocode(location)
            if location_data:
                return (location_data.latitude, location_data.longitude)
        except (GeocoderTimedOut, GeocoderUnavailable):
            print(f"Geocoding error for: {location}")
        
        return None
    
    def _calculate_influence_radius(self, event):
        # Use LLM to determine appropriate influence radius
        event_json = json.dumps(event)
        prompt = f"""
        Given this event: {event_json}
        Estimate its traffic influence radius in kilometers (1-5).
        Return only a number.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=10
        )
        
        try:
            radius = float(response.choices[0].message['content'].strip())
            return min(max(radius, 0.5), 5)  # Clamp between 0.5 and 5 km
        except:
            return 1.0  # Default radius
```

### 5. Data Storage (Day 6-7)

#### Tasks:
- Create `utils/data_storage.py` for storing and retrieving events
- Implement DataFrame-based storage for prototype
- Add serialization/deserialization to JSON
- Create data validation and cleaning functions

#### Sample Implementation:
```python
import pandas as pd
import json
from datetime import datetime
import os

class DataStorage:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self.events_file = os.path.join(data_dir, "events.json")
        self.events_df = self._load_events()
    
    def _load_events(self):
        if os.path.exists(self.events_file):
            try:
                events = pd.read_json(self.events_file)
                return events
            except:
                return pd.DataFrame(columns=["event_type", "location", "date", "coordinates", 
                                           "influence_radius", "source", "created_at"])
        else:
            return pd.DataFrame(columns=["event_type", "location", "date", "coordinates", 
                                         "influence_radius", "source", "created_at"])
    
    def save_events(self, events):
        new_events = []
        for event in events:
            event_copy = event.copy()
            event_copy["created_at"] = datetime.now().isoformat()
            new_events.append(event_copy)
        
        new_df = pd.DataFrame(new_events)
        self.events_df = pd.concat([self.events_df, new_df], ignore_index=True)
        self.events_df.to_json(self.events_file, orient="records")
    
    def get_events(self, start_date=None, end_date=None):
        # Convert string dates to datetime for filtering
        if not start_date and not end_date:
            return self.events_df.to_dict("records")
        
        filtered_df = self.events_df.copy()
        
        # Use LLM to standardize dates for comparison
        if len(filtered_df) > 0:
            filtered_df = self._standardize_dates(filtered_df)
            
            if start_date:
                filtered_df = filtered_df[filtered_df["parsed_date"] >= start_date]
            if end_date:
                filtered_df = filtered_df[filtered_df["parsed_date"] <= end_date]
        
        return filtered_df.to_dict("records")
    
    def _standardize_dates(self, df):
        # Extract all unique date references
        date_refs = df["date"].unique().tolist()
        
        # Use LLM to convert to standard format
        date_mapping = {}
        for date_ref in date_refs:
            parsed_date = self._parse_date_with_llm(date_ref)
            date_mapping[date_ref] = parsed_date
        
        # Add parsed_date column
        df["parsed_date"] = df["date"].map(date_mapping)
        return df
    
    def _parse_date_with_llm(self, date_text):
        prompt = f"""
        Convert this date reference: "{date_text}" to an ISO format date (YYYY-MM-DD).
        Use today's date as reference for relative terms like "tomorrow" or "next week".
        Return only the date in YYYY-MM-DD format, nothing else.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=20
        )
        
        date_str = response.choices[0].message['content'].strip()
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except:
            return datetime.now().date()  # Fallback to today
```

### 6. Integration Test (Day 7)

#### Tasks:
- Create basic integration tests for Phase 1 modules
- Ensure end-to-end flow from news collection to storage works
- Test with both real and mock data
- Document any issues or limitations

#### Sample Test Script:
```python
from utils.news_fetcher import NewsFetcher
from utils.event_detector import EventDetector
from utils.geo_tagger import GeoTagger
from utils.data_storage import DataStorage

def test_pipeline():
    print("Testing news data pipeline...")
    
    # Initialize components
    news_fetcher = NewsFetcher()
    event_detector = EventDetector()
    geo_tagger = GeoTagger()
    data_storage = DataStorage()
    
    # Test with mock data
    print("Testing with mock data...")
    mock_articles = news_fetcher.generate_mock_data(5)
    print(f"Generated {len(mock_articles)} mock articles")
    
    events = event_detector.detect_events(mock_articles)
    print(f"Detected {len(events)} events from mock data")
    
    geo_tagged_events = geo_tagger.geo_tag_events(events)
    print(f"Geo-tagged {len([e for e in geo_tagged_events if 'coordinates' in e and e['coordinates']])}/{len(geo_tagged_events)} events")
    
    data_storage.save_events(geo_tagged_events)
    stored_events = data_storage.get_events()
    print(f"Stored {len(stored_events)} events")
    
    # Test with real data (if API key available)
    try:
        print("\nTesting with real NewsAPI data...")
        articles = news_fetcher.fetch_news(days=3)
        print(f"Fetched {len(articles)} real articles")
        
        if articles:
            events = event_detector.detect_events(articles)
            print(f"Detected {len(events)} events from real data")
            
            geo_tagged_events = geo_tagger.geo_tag_events(events)
            print(f"Geo-tagged {len([e for e in geo_tagged_events if 'coordinates' in e and e['coordinates']])}/{len(geo_tagged_events)} events")
            
            data_storage.save_events(geo_tagged_events)
            print(f"Total stored events: {len(data_storage.get_events())}")
    except Exception as e:
        print(f"Error testing with real data: {e}")
    
    print("\nPipeline test completed!")

if __name__ == "__main__":
    test_pipeline()
```

## Phase 1 Deliverables

1. GitHub repository with complete project structure
2. Fully implemented data pipeline modules:
   - News fetcher with API integration
   - LLM-powered event detector
   - Geo-tagging system with location disambiguation
   - Data storage system
3. Integration tests for Phase 1 components
4. Documentation for setup and module usage

## Next Steps

Upon completion of Phase 1, the project will proceed to Phase 2, which focuses on building the traffic prediction engine. This will involve creating a grid system, developing the impact scoring algorithm, and implementing the core prediction functionality. 