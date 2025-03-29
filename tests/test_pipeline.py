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