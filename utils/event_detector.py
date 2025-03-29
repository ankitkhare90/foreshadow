import openai
import os
import json
from dotenv import load_dotenv

load_dotenv()

class EventDetector:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = openai.OpenAI(api_key=self.api_key)
    
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
        1. Event type (concert, sport event, road closure, construction, festival, etc.)
        2. Location (as specific as possible such as street name, pincode, landmark, etc.)
        3. Date (as specific as possible such as 01-01-2025 etc.)
        4. Time (as specific as possible such as 10:00 AM, 10:00 PM, etc.)
        5. Expected attendance or scale (if mentioned)
        
        Return JSON format only, with no explanation:
        [
          {{
            "event_type": "...",
            "location": "...",
            "date": "...",
            "time": "...",
            "scale": "..."
          }}
        ]
        
        If no traffic-related events are found, return an empty array.
        
        Text: {text}
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_completion_tokens=2048,
            )

            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            print("Error parsing JSON response from LLM")
            return []
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return []
