import requests
import json
import time
from datetime import datetime

class InstagramMonitor:
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

    def fetch_user_stats(self):
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
            user_data = data['data']['user']
            
            return {
                'username': user_data['username'],
                'full_name': user_data['full_name'],
                'follower_count': user_data['follower_count'],
                'following_count': user_data['following_count'],
                'media_count': user_data['media_count'],
                'biography': user_data['biography'],
                'profile_pic_url': user_data['profile_pic_url'],
                'hd_profile_pic_url': user_data['hd_profile_pic_url_info']['url'],
                'is_private': user_data['is_private'],
                'is_verified': user_data['is_verified'],
                'category': user_data['category'],
                'external_url': user_data['external_url'],
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None 