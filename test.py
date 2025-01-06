import requests
import json
import time
from datetime import datetime

class InstagramFollowerMonitor:
    def __init__(self, user_id, notification_interval=100):
        self.user_id = user_id
        self.notification_interval = notification_interval
        self.last_count = 0
        self.headers = {
            'authority': 'www.instagram.com',
            'accept': '*/*',
            'accept-language': 'en-GB,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://www.instagram.com',
            'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15',
            'x-fb-friendly-name': 'PolarisProfilePageContentQuery',
        }
        
    def fetch_follower_count(self):
        payload = {
            'doc_id': '9383802848352200',
            'variables': json.dumps({
                "id": self.user_id,
                "render_surface": "PROFILE"
            })
        }
        
        try:
            response = requests.post(
                'https://www.instagram.com/graphql/query',
                headers=self.headers,
                data=payload
            )
            data = response.json()
            return data['data']['user']['follower_count']
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None

    def check_and_notify(self):
        current_count = self.fetch_follower_count()
        
        if current_count is None:
            return
        
        if self.last_count == 0:
            self.last_count = current_count
            print(f"Initial follower count: {current_count}")
            return
            
        difference = current_count - self.last_count
        
        if abs(difference) >= self.notification_interval:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if difference > 0:
                print(f"[{timestamp}] 🎉 Follower count increased by {difference}! New count: {current_count}")
            else:
                print(f"[{timestamp}] 📉 Follower count decreased by {abs(difference)}. New count: {current_count}")
            self.last_count = current_count

    def start_monitoring(self, check_interval=300):
        print(f"Starting to monitor follower count for user ID: {self.user_id}")
        while True:
            self.check_and_notify()
            time.sleep(check_interval)

# Usage
monitor = InstagramFollowerMonitor("51651500950")  # Your friend's user ID
monitor.start_monitoring(check_interval=300)  # Check every 5 minutes