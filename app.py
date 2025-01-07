from flask import Flask, jsonify, request, render_template, redirect
from flask_cors import CORS
from instagram_monitor import InstagramMonitor
from datetime import datetime, timezone
import json
import os
import pytz

app = Flask(__name__)
CORS(app)
app.url_map.strict_slashes = False
monitors = {}

@app.route('/amishi/api/update_thresholds/', methods=['POST'])
def update_thresholds():
    data = request.json
    user_id = data.get('user_id')
    
    if user_id in monitors:
        pass
        
    return jsonify({
        'status': 'success',
        'message': 'Thresholds updated successfully'
    })

@app.route('/amishi/api/start_monitoring/', methods=['POST'])
def start_monitoring():
    data = request.json
    user_id = data.get('user_id')
    
    if user_id not in monitors:
        monitors[user_id] = InstagramMonitor(user_id)
    
    # Fetch initial stats
    stats = monitors[user_id].fetch_user_stats()
    if not stats:
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch initial stats'
        }), 400
    
    save_history(user_id, stats)
    
    return jsonify({
        'status': 'success',
        'message': f'Started monitoring user ID: {user_id}',
        'stats': stats
    })

@app.route('/amishi/api/data/<user_id>/', methods=['GET'])
def get_data(user_id):
    if user_id not in monitors:
        monitors[user_id] = InstagramMonitor(user_id)
    
    stats = monitors[user_id].fetch_user_stats()
    if stats:
        save_history(user_id, stats)
        history = load_history().get(user_id, [])
        return jsonify({
            'stats': stats,
            'history': history
        })
    return jsonify({'stats': None, 'history': []})

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
    
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)
    
    history[user_id].append({
        'count': stats['follower_count'],
        'timestamp': current_time.isoformat()
    })
    
    # Keep only last 7 days of data
    week_data = history[user_id][-2016:]  # 7 days * 24 hours * 12 updates per hour
    history[user_id] = week_data
    
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f)

if __name__ == '__main__':
    app.run(debug=True) 