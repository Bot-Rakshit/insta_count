from flask import Flask, jsonify, request, render_template, redirect
from flask_cors import CORS
from instagram_monitor import InstagramMonitor
from datetime import datetime
import json
from pywebpush import webpush, WebPushException
import os

app = Flask(__name__)
CORS(app)
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
@app.route('/amishi/api/vapid-public-key')
def get_vapid_public_key():
    return jsonify({'publicKey': app.config['VAPID_PUBLIC_KEY']})

@app.route('/amishi/api/update_thresholds', methods=['POST'])
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

@app.route('/amishi/api/start_monitoring', methods=['POST'])
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

@app.route('/amishi/api/stats/<user_id>', methods=['GET'])
def get_stats(user_id):
    if user_id not in monitors:
        monitors[user_id] = InstagramMonitor(user_id)
    
    stats = monitors[user_id].fetch_user_stats()
    return jsonify(stats)

@app.route('/amishi/api/subscribe', methods=['POST'])
def subscribe():
    subscription_info = request.json
    
    try:
        webpush(
            subscription_info=subscription_info,
            data="Test notification",
            vapid_private_key=app.config['VAPID_PRIVATE_KEY'],
            vapid_claims=app.config['VAPID_CLAIMS']
        )
        return jsonify({'status': 'success'})
    except WebPushException as ex:
        return jsonify({'status': 'failed', 'message': str(ex)}), 500

# Add root route
@app.route('/amishi')
def index():
    return render_template('index.html')

# Redirect root to /amishi
@app.route('/')
def redirect_to_amishi():
    return redirect('/amishi')

if __name__ == '__main__':
    app.run(debug=True) 