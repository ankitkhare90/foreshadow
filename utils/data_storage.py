import pandas as pd
import json
import os
import openai
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class DataStorage:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self.events_file = os.path.join(data_dir, "events.json")
        self.events_df = self._load_events()
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = openai.OpenAI(api_key=self.api_key)
    
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
        date_refs = df["date"].dropna().unique().tolist()
        
        # Use LLM to convert to standard format
        date_mapping = {}
        for date_ref in date_refs:
            parsed_date = self._parse_date_with_llm(date_ref)
            date_mapping[date_ref] = parsed_date
        
        # Add parsed_date column
        df["parsed_date"] = df["date"].map(date_mapping)
        return df
    
    def _parse_date_with_llm(self, date_text):
        if not date_text:
            return datetime.now().date()
            
        prompt = f"""
        Convert this date reference: "{date_text}" to an ISO format date (YYYY-MM-DD).
        Use today's date as reference for relative terms like "tomorrow" or "next week".
        Return only the date in YYYY-MM-DD format, nothing else.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=20
            )
            
            date_str = response.choices[0].message.content.strip()
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception as e:
            print(f"Error parsing date: {e}")
            return datetime.now().date()  # Fallback to today 