import os
import socket
import requests
import json
import logging
from typing import Tuple, Optional, Dict, Any, List
import tkinter as tk
from tkinter.ttk import Notebook
import myNotebook as nb
from config import config
from config import appname
import plug
from collections import deque

PLUGIN_NAME = "ED-KillTracker"
PLUGIN_VERSION = "0.9.0"

# Supported event types
SUPPORTED_EVENTS = [
    'Bounty',
    'MissionAbandoned',
    'MissionAccepted',
    'MissionCompleted',
    'MissionFailed',
    'Missions'
]

# Event history buffer for context analysis
EVENT_HISTORY_SIZE = 10
event_history = deque(maxlen=EVENT_HISTORY_SIZE)

# Setup logger
plugin_name = os.path.basename(os.path.dirname(__file__))
logger = logging.getLogger(f'{appname}.{plugin_name}')

# Initialize logger if needed
if not logger.hasHandlers():
    level = logging.DEBUG
    logger.setLevel(level)
    logger_channel = logging.StreamHandler()
    logger_formatter = logging.Formatter(f'%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d:%(funcName)s: %(message)s')
    logger_formatter.default_time_format = '%Y-%m-%d %H:%M:%S'
    logger_formatter.default_msec_format = '%s.%03d'
    logger_channel.setFormatter(logger_formatter)
    logger.addHandler(logger_channel)

logging_var = False


# Construct the server URL
server_url = "https://ed-killtracker-production.up.railway.app/"

def plugin_start3(plugin_dir: str) -> Tuple[str, str, str]:
    """Called when the plugin is enabled."""
    if logging_var:
        logger.info("KillsTracker plugin started")
        logger.info(f"Server URL: {server_url}")
    
    return PLUGIN_NAME

def send_event_data(event_data):
    """Send event data to the server."""
    try:
        if event_data['event'] == 'Bounty':
            response = requests.post(server_url+"/new_kill", json=event_data, verify=False)
            response.raise_for_status()
            
            if logging_var:
                logger.info("Bounty event data sent successfully")
        elif event_data['event'] == 'MissionAccepted':
            response = requests.post(server_url+"/new_mission", json=event_data, verify=False)
            response.raise_for_status()
            
            if logging_var:
                logger.info("Mission accept event data sent successfully")
        elif event_data['event'] == 'MissionAbandoned' or event_data['event'] == 'MissionFailed':
            response = requests.post(server_url+"/fail_mission", json=event_data, verify=False)
            response.raise_for_status()
            
            if logging_var:
                logger.info("Mission fail event data sent successfully")
        elif event_data['event'] == 'MissionCompleted':
            response = requests.post(server_url+"/complete_mission", json=event_data, verify=False)
            response.raise_for_status()
            
            if logging_var:
                logger.info("Mission complete event data sent successfully")

        elif event_data['event'] == 'Missions':
            response = requests.post(server_url+"/reload_missions", json=event_data, verify=False)
            response.raise_for_status()
            
            if logging_var:
                logger.info("Bounty event data sent successfully")
    except requests.exceptions.RequestException as e:
        if logging_var:
            logger.error(f'Web call failed: {str(e)}')

def test_http_post():
    """Send a test message to verify the server connection."""
    test_data = {'test': 'This is a test post from the EDMC plugin.'}
    send_event_data(test_data)

def journal_entry(cmdr, is_beta, system, station, entry, state):
    """Process journal entries and send relevant ones to the server with improved PowerPlay tracking."""
    global event_history
    
    # Add to event history for context analysis
    event_history.append(entry)
    
    event = entry.get('event')
    
    if event not in SUPPORTED_EVENTS:
        return
    
    if logging_var:
        logger.info(f'Detected event: {event}')
        logger.info(entry)
    
    event_data = {
        'event': event,
        'timestamp': entry.get('timestamp', ''),
        'system': system,
        'station': station,
        'cmdr': cmdr,
        'entry': entry  # Send the raw event data for server-side processing
    }
    
    send_event_data(event_data)