# Traffic Prediction Tool

A predictive system that correlates news events with traffic patterns to forecast congestion in specific areas.

## Features

- Fetches news data related to traffic events using NewsAPI
- Uses OpenAI's GPT-4 to detect traffic-impacting events from news articles
- Geotags events to specific locations
- Visualizes events on an interactive map
- Predicts traffic impact using event influence zones

## Project Setup

### Requirements

- Python 3.8+
- NewsAPI API key
- OpenAI API key

### Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   uv pip install -r requirements.txt
   ```
4. Create a `.env` file in the project root with your API keys:
   ```
   NEWSAPI_API_KEY=your-newsapi-key
   OPENAI_API_KEY=your-openai-key
   ```

### Running the Application

Start the Streamlit application:
```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501`.

### Testing

Run the test pipeline to verify that the components are working correctly:
```bash
python tests/test_pipeline.py
```

## Project Structure

- `app.py`: Main Streamlit application
- `utils/`: Core functionality modules
  - `news_fetcher.py`: Fetches news from NewsAPI
  - `event_detector.py`: Uses OpenAI to detect events from news
  - `geo_tagger.py`: Tags events with geographic coordinates
  - `data_storage.py`: Stores and retrieves event data
- `tests/`: Test scripts
- `data/`: Directory for storing data files

## Phase 1 Implementation

Phase 1 focuses on setting up the data pipeline:
1. News data collection from APIs
2. Event detection using OpenAI LLM
3. Geographic tagging of events
4. Basic data storage system

## Next Steps

- Phase 2: Traffic prediction engine
- Phase 3: Enhanced user interface and visualizations
- Phase 4: Testing, optimization, and deployment 