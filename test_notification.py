import requests
import json

def send_test_notification():
    # Your server URL
    server_url = "http://your_domain.com"  # Change this to your domain
    
    # First get the public key
    response = requests.get(f"{server_url}/api/vapid-public-key")
    vapid_public_key = response.json()['publicKey']
    
    # Create a test subscription
    subscription_info = {
        "endpoint": "https://updates.push.services.mozilla.com/wpush/v2/YOUR_ENDPOINT",
        "keys": {
            "auth": "YOUR_AUTH_SECRET",
            "p256dh": "YOUR_P256DH_KEY"
        }
    }
    
    # Send the subscription to your server
    response = requests.post(
        f"{server_url}/api/subscribe",
        json=subscription_info,
        headers={'Content-Type': 'application/json'}
    )
    
    print("Response:", response.json())

if __name__ == "__main__":
    send_test_notification() 