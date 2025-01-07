import requests
import json
import time
from datetime import datetime

class InstagramMonitor:
    def __init__(self, user_id, increase_threshold=100, decrease_threshold=100):
        self.user_id = user_id
        self.increase_threshold = increase_threshold
        self.decrease_threshold = decrease_threshold
        self.last_count = 0
        self.headers = {
            'authority': 'www.instagram.com',
            'accept': '*/*',
            'accept-language': 'en-GB,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://www.instagram.com',
            'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15',
            'x-fb-friendly-name': 'PolarisProfilePageContentQuery',
            'x-ig-app-id': '936619743392459',
            'x-requested-with': 'XMLHttpRequest'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def fetch_user_stats(self):
        print(f"Fetching stats for user {self.user_id}")  # Debug log
        payload = {
            'doc_id': '9383802848352200',
            'variables': json.dumps({
                "id": self.user_id,
                "render_surface": "PROFILE"
            })
        }
        
        try:
            response = self.session.post(
                'https://www.instagram.com/graphql/query',
                data=payload
            )
            print(f"Response status: {response.status_code}")  # Debug log
            print(f"Response content: {response.text[:200]}")  # Debug log first 200 chars
            
            data = response.json()
            user_data = data['data']['user']
            
            return {
                'username': user_data['username'],
                'follower_count': user_data['edge_followed_by']['count'],
                'following_count': user_data['edge_follow']['count'],
                'media_count': user_data['edge_owner_to_timeline_media']['count'],
                'biography': user_data['biography'],
                'external_url': user_data.get('external_url', ''),
                'is_private': user_data['is_private'],
                'is_verified': user_data['is_verified'],
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error fetching Instagram data: {str(e)}")  # Debug log
            return None 

    def check_and_notify(self, current_count):
        if self.last_count == 0:
            self.last_count = current_count
            return None
            
        difference = current_count - self.last_count
        
        if difference >= self.increase_threshold:
            self.last_count = current_count
            return {
                'type': 'increase',
                'difference': difference,
                'current_count': current_count
            }
        elif abs(difference) >= self.decrease_threshold:
            self.last_count = current_count
            return {
                'type': 'decrease',
                'difference': abs(difference),
                'current_count': current_count
            }
        
        return None 