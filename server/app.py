from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
import json
import os
import logging
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
# Fix for threading issues - don't use eventlet
socketio = SocketIO(app, async_mode='threading')
localhost = False  # Set to False to use external IP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('killtracker_server')

def to_title_case(name):
    """Convert string to title case (e.g. 'anaconda' -> 'Anaconda')"""
    if not name or name == 'Unknown':
        return name
    return name.title()

def normalize_ship_name(ship_name, raw_name=None):
    """Convert ship name to standardized format matching image filenames"""
    # First try to use localized name if available
    if ship_name and ship_name != 'Unknown':
        # Convert to lowercase and remove special characters
        normalized = ship_name.lower().replace(' ', '-').replace('_', '-')
        normalized = ''.join(c for c in normalized if c.isalnum() or c == '-')
        
        # Remove any remaining special cases
        normalized = normalized.replace('type-', 'type').replace('mk-', 'mk')
        return normalized
    
    # Fall back to raw name if no localized name
    if raw_name:
        return raw_name.lower().replace(' ', '-').replace('_', '-')
    
    return 'unknown-ship'

def process_bounty_event(entry, data):
    """Process Bounty events and format for the client"""
    # Get display name - prefer localized, fall back to raw
    display_name = entry.get('Target_Localised', 
                           entry.get('Ship_Localised',
                           entry.get('Target',
                           entry.get('Ship', 'Unknown'))))
    
    # Get raw name for normalization
    raw_name = entry.get('Target', entry.get('Ship', ''))
    normalized_name = normalize_ship_name(display_name, raw_name)
    
    # Apply title case to display names for better readability
    display_name = to_title_case(display_name)
    
    processed_data = {
        'timestamp': entry.get('timestamp', ''),
        'event': 'Bounty',
        'eventType': 'Bounty',
        'shipname': display_name,
        'Ship': display_name,
        'shipImageFileName': normalized_name,
        'bountyAmount': entry.get('TotalReward', 0),
        'VictimFaction': entry.get('VictimFaction', 'Unknown'),
        'Faction': entry.get('VictimFaction', 'Unknown'),
        'Rewards': entry.get('Rewards', []),
        'system': data.get('system', ''),
        'station': data.get('station', ''),
        'cmdr': data.get('cmdr', '')
    }
    return processed_data

def process_mission_accepted_event(entry, data):
    processed_data = {
        'ID': entry.get('MissionID', None),
        'isMassacre': "Massacre" in entry.get("Name", "Unknown Mission"),
        'faction': entry.get('Faction', 'Unknown Faction'),
        'target': entry.get('TargetFaction', 'Unknown Faction'),
        'kills': entry.get('KillCount', 0),
        'reward': entry.get('Reward', 0)
    }
    return processed_data

def process_mission_fail_event(entry, data):
    processed_data = {
        'ID': entry.get('MissionID', None)
    }
    return processed_data

def process_mission_complete_event(entry, data):
    processed_data = {
        'ID': entry.get('MissionID', None),
        'reward': entry.get('Reward', 0)
    }
    return processed_data

@app.route('/')
def home():
    return render_template('table.html')

@app.route('/new_kill', methods=['POST'])
def update_kills():
    try:
        data = request.json
        print(f"Received event: {data.get('event', 'Unknown')}")
        
        # Extract the raw entry data
        entry = data.get('entry', {})
        event_type = entry.get('event', '')
        
        # Empty response for unsupported event types
        processed_data = None
        
        # Process based on event type
        if event_type == 'Bounty':
            processed_data = process_bounty_event(entry, data)
            print(processed_data)
            socketio.emit('new_kill', processed_data)
            
        elif event_type == 'test':
            socketio.emit('new_test', data)
            return jsonify({'success': True, 'data': data})
            
        # Return a response based on whether the event was processed
        if processed_data:
            return jsonify({'success': True, 'data': processed_data})
        else:
            return jsonify({'success': False, 'message': f'Unsupported event type: {event_type}'})
    except Exception as e:
        logger.error(f"Error processing event: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})
    
@app.route('/new_mission', methods=['POST'])
def add_mission():
    try:
        data = request.json
        entry = data.get('entry', {})
        print(f"Received event: {data.get('event', 'Unknown')}")
        processed_data = process_mission_accepted_event(entry, data)
        socketio.emit('new_mission', processed_data)
        return jsonify({'success': True, 'data': processed_data})
    except Exception as e:
        logger.error(f"Error processing event: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})
    
@app.route('/fail_mission', methods=['POST'])
def fail_mission():
    try:
        data = request.json
        entry = data.get('entry', {})
        print(f"Received event: {data.get('event', 'Unknown')}")
        processed_data = process_mission_fail_event(entry, data)
        print(processed_data)
        socketio.emit('fail_mission', processed_data)
        return jsonify({'success': True, 'data': processed_data})
    except Exception as e:
        logger.error(f"Error processing event: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})
    
@app.route('/complete_mission', methods=['POST'])
def complete_mission():
    try:
        data = request.json
        entry = data.get('entry', {})
        print(f"Received event: {data.get('event', 'Unknown')}")
        processed_data = process_mission_complete_event(entry, data)
        print(processed_data)
        socketio.emit('complete_mission', processed_data)
        return jsonify({'success': True, 'data': processed_data})
    except Exception as e:
        logger.error(f"Error processing event: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})
    
@app.route('/reload_missions', methods=['POST'])
def reload_missions():
    try:
        data = request.json
        entry = data.get('entry', {})
        print(f"Received event: {data.get('event', 'Unknown')}")
        for mission in entry.get('Active', []):
            print(mission)
            processed_data = process_mission_accepted_event(mission, {})
            #socketio.emit('new_mission', processed_data)
        for mission in entry.get('Complete', []):
            processed_data = process_mission_accepted_event(mission, {})
            #socketio.emit('new_mission', processed_data)
        return jsonify({'success': True, 'data': None})
    except Exception as e:
        logger.error(f"Error processing event: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/test_server', methods=['GET'])
def test_server():    
    socketio.emit('test_server')
    return jsonify({'success': True})

if __name__ == '__main__': 
    host = '127.0.0.1' if localhost else '0.0.0.0'
    port = 5050
    
    logger.info(f"Starting server on {host}:{port}")
    socketio.run(app, host=host, port=port, debug=True)
