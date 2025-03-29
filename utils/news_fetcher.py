import requests
import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

class NewsFetcher:
    def __init__(self):
        self.api_key = os.getenv("NEWSAPI_API_KEY")
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
            {"type": "festival", "location": "Golden Gate Park", "date": "this weekend"},
            {"type": "marathon", "location": "Market Street", "date": "Sunday morning"}
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