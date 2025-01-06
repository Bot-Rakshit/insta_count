from flask import Flask, jsonify, request, render_template, redirect
from flask_cors import CORS
from instagram_monitor import InstagramMonitor
from datetime import datetime
import json
from pywebpush import webpush, WebPushException
import os

app = Flask(__name__)
CORS(app)
app.url_map.strict_slashes = False
monitors = {}

def load_vapid_keys():
    try:
        with open('vapid_keys.txt', 'r') as f:
            content = f.read()
            public_key = content.split('Public Key:\n')[1].split('\n\n')[0].strip()
            private_key = content.split('Private Key:\n')[1].strip()
        return public_key, private_key
    except Exception as e:
        print(f"Error loading VAPID keys: {e}")
        return None, None

# Update the app configuration
public_key, private_key = load_vapid_keys()
app.config['VAPID_PUBLIC_KEY'] = public_key or os.environ.get('VAPID_PUBLIC_KEY')
app.config['VAPID_PRIVATE_KEY'] = private_key or os.environ.get('VAPID_PRIVATE_KEY')
app.config['VAPID_CLAIMS'] = {
    'sub': 'singhrakshit003@gmail.com',  # Replace with your email
    'aud': 'https://fcm.googleapis.com'  # Required for Firebase Cloud Messaging
}

# Add a route to get the public key
@app.route('/amishi/api/vapid-public-key/')
def get_vapid_public_key():
    return jsonify({'publicKey': app.config['VAPID_PUBLIC_KEY']})

@app.route('/amishi/api/update_thresholds/', methods=['POST'])
def update_thresholds():
    data = request.json
    user_id = data.get('user_id')
    increase_threshold = data.get('increase_threshold', 100)
    decrease_threshold = data.get('decrease_threshold', 100)
    
    if user_id in monitors:
        monitors[user_id].increase_threshold = increase_threshold
        monitors[user_id].decrease_threshold = decrease_threshold
        
    return jsonify({
        'status': 'success',
        'message': 'Thresholds updated successfully'
    })

@app.route('/amishi/api/start_monitoring/', methods=['POST'])
def start_monitoring():
    data = request.json
    user_id = data.get('user_id')
    increase_threshold = data.get('increase_threshold', 100)
    decrease_threshold = data.get('decrease_threshold', 100)
    
    if user_id not in monitors:
        monitors[user_id] = InstagramMonitor(
            user_id, 
            increase_threshold=int(increase_threshold),
            decrease_threshold=int(decrease_threshold)
        )
    
    return jsonify({
        'status': 'success',
        'message': f'Started monitoring user ID: {user_id}'
    })

@app.route('/amishi/api/stats/<user_id>/', methods=['GET'])
def get_stats(user_id):
    if user_id not in monitors:
        monitors[user_id] = InstagramMonitor(user_id)
    
    stats = monitors[user_id].fetch_user_stats()
    return jsonify(stats)

@app.route('/amishi/api/subscribe/', methods=['POST'])
def subscribe():
    subscription_info = request.json
    
    try:
        # Save the subscription info for later use
        with open('last_subscription.json', 'w') as f:
            json.dump(subscription_info, f)
        
        webpush(
            subscription_info=subscription_info,
            data="Test notification",
            vapid_private_key=app.config['VAPID_PRIVATE_KEY'],
            vapid_claims=app.config['VAPID_CLAIMS']
        )
        return jsonify({'status': 'success'})
    except WebPushException as ex:
        return jsonify({'status': 'failed', 'message': str(ex)}), 500

@app.route('/amishi/api/test-notification/')
def test_notification():
    try:
        # Get all active monitors
        for user_id, monitor in monitors.items():
            stats = monitor.fetch_user_stats()
            if stats:
                message = f"Test Notification!\n{stats['username']} has {stats['follower_count']} followers"
                # Try to read subscription info from the last successful subscription
                try:
                    with open('last_subscription.json', 'r') as f:
                        subscription_info = json.load(f)
                        webpush(
                            subscription_info=subscription_info,
                            data=message,
                            vapid_private_key=app.config['VAPID_PRIVATE_KEY'],
                            vapid_claims=app.config['VAPID_CLAIMS']
                        )
                except Exception as e:
                    return jsonify({'status': 'error', 'message': 'No active subscription found. Please enable notifications first.'}), 400
        
        return jsonify({'status': 'success', 'message': 'Test notification sent!'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Add root route
@app.route('/')
def root():
    return "Welcome to Instagram Monitor API"

@app.route('/amishi/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True) 