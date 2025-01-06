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
        print(f"Received subscription info: {subscription_info}")  # Debug print
        
        # Validate subscription info
        if not subscription_info or 'endpoint' not in subscription_info or 'keys' not in subscription_info:
            print("Invalid subscription format")
            return jsonify({
                'status': 'error',
                'message': 'Invalid subscription format'
            }), 400
        
        # Save the subscription info for later use
        print(f"Saving subscription to {os.path.abspath('last_subscription.json')}")
        with open('last_subscription.json', 'w') as f:
            json.dump(subscription_info, f)
        
        # Verify the file was saved
        if not os.path.exists('last_subscription.json'):
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
        if not os.path.exists('last_subscription.json'):
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
        if os.path.exists('last_subscription.json'):
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

if __name__ == '__main__':
    app.run(debug=True) 