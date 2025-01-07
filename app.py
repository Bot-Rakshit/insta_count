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

# Print working directory and permissions at startup
print(f"Working Directory: {os.getcwd()}")
print(f"Directory Permissions: {oct(os.stat('.').st_mode)[-3:]}")
print(f"User Running Process: {os.getuid()}:{os.getgid()}")

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
    if stats:
        save_history(user_id, stats)
    return jsonify(stats)

@app.route('/amishi/api/subscribe/', methods=['POST'])
def subscribe():
    subscription_info = request.json
    
    try:
        print(f"Received subscription info: {subscription_info}")  # Debug print
        
        # Use absolute path in the application directory
        subscription_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'last_subscription.json')
        print(f"Will save subscription to: {subscription_file}")
        
        # Validate subscription info
        if not subscription_info or 'endpoint' not in subscription_info or 'keys' not in subscription_info:
            print("Invalid subscription format")
            return jsonify({
                'status': 'error',
                'message': 'Invalid subscription format'
            }), 400
        
        # Save the subscription info for later use
        print(f"Saving subscription to {subscription_file}")
        with open(subscription_file, 'w') as f:
            json.dump(subscription_info, f)
        # Verify the file was saved
        if not os.path.exists(subscription_file):
            print("Failed to save subscription file")
            return jsonify({
                'status': 'error',
                'message': 'Failed to save subscription'
            }), 500
        
        webpush(
            subscription_info=subscription_info,
            data="Notifications enabled successfully! 🎉",
            vapid_private_key=app.config['VAPID_PRIVATE_KEY'],
            vapid_claims=app.config['VAPID_CLAIMS']
        )
        
        # Read back the saved subscription to verify
        with open('last_subscription.json', 'r') as f:
            saved_subscription = json.load(f)
            print(f"Verified saved subscription: {saved_subscription}")
        
        return jsonify({
            'status': 'success',
            'message': 'Subscription successful',
            'details': {
                'subscription': subscription_info,
                'vapid_claims': app.config['VAPID_CLAIMS'],
                'file_path': os.path.abspath('last_subscription.json')
            }
        })
    except WebPushException as ex:
        print(f"WebPush Error: {str(ex)}")  # Debug print
        return jsonify({'status': 'failed', 'message': str(ex)}), 500
    except Exception as e:
        print(f"General Error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/amishi/api/test-notification/')
def test_notification():
    try:
        subscription_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'last_subscription.json')
        if not os.path.exists(subscription_file):
            return jsonify({
                'status': 'error',
                'message': 'No subscription file found. Please enable notifications first.'
            }), 400
        
        if not monitors:
            return jsonify({
                'status': 'error',
                'message': 'No active monitors found. Please start monitoring first.'
            }), 400
        
        for user_id, monitor in monitors.items():
            stats = monitor.fetch_user_stats()
            if stats:
                message = f"Test Notification!\n{stats['username']} has {stats['follower_count']} followers"
                try:
                    with open('last_subscription.json', 'r') as f:
                        subscription_info = json.load(f)
                        print(f"Sending notification with subscription: {subscription_info}")  # Debug print
                        webpush(
                            subscription_info=subscription_info,
                            data=message,
                            vapid_private_key=app.config['VAPID_PRIVATE_KEY'],
                            vapid_claims=app.config['VAPID_CLAIMS']
                        )
                except FileNotFoundError:
                    return jsonify({'status': 'error', 'message': 'Subscription file not found'}), 400
                except json.JSONDecodeError:
                    return jsonify({'status': 'error', 'message': 'Invalid subscription data'}), 400
                except Exception as e:
                    return jsonify({'status': 'error', 'message': f'Error sending notification: {str(e)}'}), 500
        
        return jsonify({
            'status': 'success',
            'message': 'Test notification sent!',
            'details': {
                'subscription': subscription_info,
                'vapid_claims': app.config['VAPID_CLAIMS']
            }
        })
    except Exception as e:
        print(f"Error in test_notification: {str(e)}")  # Debug print
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/amishi/api/subscription-status/')
def subscription_status():
    try:
        subscription_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'last_subscription.json')
        if os.path.exists(subscription_file):
            with open('last_subscription.json', 'r') as f:
                subscription = json.load(f)
            return jsonify({
                'status': 'success',
                'message': 'Subscription found',
                'details': {
                    'subscription': subscription,
                    'file_path': os.path.abspath('last_subscription.json')
                }
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'No subscription found',
                'details': {
                    'working_directory': os.getcwd(),
                    'file_path': os.path.abspath('last_subscription.json')
                }
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Add root route
@app.route('/')
def root():
    return "Welcome to Instagram Monitor API"

@app.route('/amishi/')
def index():
    return render_template('index.html')

HISTORY_FILE = 'follower_history.json'

def load_history():
    try:
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_history(user_id, stats):
    history = load_history()
    if user_id not in history:
        history[user_id] = []
    
    history[user_id].append({
        'count': stats['follower_count'],
        'timestamp': datetime.now().isoformat()
    })
    
    # Keep only last 7 days of data
    week_data = history[user_id][-2016:]  # 7 days * 24 hours * 12 updates per hour
    history[user_id] = week_data
    
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f)

@app.route('/amishi/api/history/<user_id>/')
def get_history(user_id):
    history = load_history()
    return jsonify(history.get(user_id, []))

if __name__ == '__main__':
    app.run(debug=True) 