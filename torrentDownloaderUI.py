import libtorrent as lt
import time
import os
import sys
import subprocess
import logging
from flask import Flask, render_template, request, jsonify
from threading import Thread

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG to capture all logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Log to console
        logging.FileHandler('torrent_downloader.log')  # Log to file
    ]
)

# Create a logger for this module
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
# Set log level for Flask to WARNING to reduce noise
logging.getLogger('werkzeug').setLevel(logging.WARNING)
import json
import socket
import requests

app = Flask(__name__)

# Get local IP address
def get_local_ip():
    try:
        # Create a socket to get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

# Global variables to track downloads
active_downloads = {}
completed_torrents_info = [] # Store info of completed torrents (name, size, etc.)
completed_torrents_ids = set() # To avoid duplicate entries in completed_torrents_info by torrent ID or unique name
added_magnets = [] # Store previously added magnet links
download_session = lt.session()
download_session.listen_on(6881, 6891)
# Set default upload speed limit to 100 KB/s
default_upload_limit_kb = 100
download_session.upload_rate_limit = default_upload_limit_kb * 1024
print(f"Default upload rate limit set to: {default_upload_limit_kb} KB/s ({download_session.upload_rate_limit} bytes/s)")
local_ip = get_local_ip() # Initial fetch

@app.route('/')
def index():
    return render_template('index.html', ip_address=local_ip)

def download_torrent(magnet_link_or_file_path, save_path="."):
    """Downloads a torrent and returns the handle"""
    try:
        # Validate input
        if not magnet_link_or_file_path:
            app.logger.error("No magnet link or file path provided")
            return None
            
        # Create save directory if it doesn't exist
        try:
            os.makedirs(save_path, exist_ok=True)
            app.logger.debug(f"Save directory created/verified: {save_path}")
        except Exception as e:
            app.logger.error(f"Failed to create save directory {save_path}: {str(e)}")
            return None
    
        handle = None
        
        try:
            if magnet_link_or_file_path.startswith("magnet:"):
                app.logger.debug(f"Adding magnet link: {magnet_link_or_file_path[:60]}...")
                
                # Create add_torrent_params object
                params = lt.add_torrent_params()
                
                # Parse magnet URI
                params = lt.parse_magnet_uri(magnet_link_or_file_path)
                params.save_path = save_path
                params.storage_mode = lt.storage_mode_t.storage_mode_sparse
                
                # Set flags
                params.flags |= lt.torrent_flags.duplicate_is_error
                params.flags &= ~lt.torrent_flags.paused
                params.flags &= ~lt.torrent_flags.auto_managed
                
                # Add the torrent to the session
                handle = download_session.add_torrent(params)
                
                if not handle or not handle.is_valid():
                    app.logger.error("Failed to create valid handle from magnet link")
                    return None
                
                # Force a recheck to verify existing files
                app.logger.debug("Forcing recheck of existing files...")
                handle.force_recheck()
                
                # Resume the torrent after recheck
                handle.resume()
                app.logger.info(f"Successfully added magnet link, handle: {handle}")
                
            elif os.path.exists(magnet_link_or_file_path) and magnet_link_or_file_path.endswith(".torrent"):
                app.logger.debug(f"Adding .torrent file: {magnet_link_or_file_path}")
                
                # Create add_torrent_params object
                params = lt.add_torrent_params()
                
                # Set torrent info and parameters
                params.ti = lt.torrent_info(magnet_link_or_file_path)
                params.save_path = save_path
                params.storage_mode = lt.storage_mode_t.storage_mode_sparse
                
                # Set flags
                params.flags |= lt.torrent_flags.duplicate_is_error
                params.flags &= ~lt.torrent_flags.paused
                params.flags &= ~lt.torrent_flags.auto_managed
                
                # Add the torrent to the session
                handle = download_session.add_torrent(params)
                
                # Force a recheck to verify existing files
                handle.force_recheck()
                handle.resume()
                app.logger.info(f"Successfully added .torrent file, handle: {handle}")
                
            else:
                error_msg = f"Invalid magnet link or .torrent file: {magnet_link_or_file_path}"
                app.logger.error(error_msg)
                return None
                
            if handle and handle.is_valid():
                app.logger.debug(f"Torrent handle is valid: {handle}")
                return handle
                
            app.logger.error("Handle is invalid after creation")
            return None
            
        except Exception as e:
            app.logger.error(f"Error in download_torrent: {str(e)}", exc_info=True)
            return None
            
    except Exception as e:
        app.logger.error(f"Unexpected error in download_torrent: {str(e)}", exc_info=True)
        return None

@app.route('/control_torrent/<handle_id>/<action>', methods=['POST'])
def control_torrent(handle_id, action):
    if handle_id not in active_downloads:
        return jsonify({'success': False, 'error': 'Torrent not found'})
    
    handle = active_downloads[handle_id]['handle']
    
    try:
        if action == 'pause':
            if handle.status().paused:
                handle.resume()
            else:
                handle.pause()
        elif action == 'delete':
            handle.remove()
            del active_downloads[handle_id]
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Add is_paused to status info in update_torrent_status function
def update_torrent_status():
    while True:
        for handle_id, info in list(active_downloads.items()):
            handle = info['handle']
            if not handle.is_valid():
                continue
                
            s = handle.status()
            
            # Update status information
            state_str = ['queued', 'checking', 'downloading metadata',
                        'downloading', 'finished', 'seeding', 'allocating']
            
            status_info = {
                'name': s.name if s.has_metadata else "Fetching metadata...",
                'progress': round(s.progress * 100, 2),
                'download_rate': round(s.download_rate / 1000, 2),  # KB/s
                'upload_rate': round(s.upload_rate / 1000, 2),      # KB/s
                'num_peers': s.num_peers,
                'state': state_str[s.state] if s.state < len(state_str) else "unknown",
                'is_finished': s.is_finished,
                'is_paused': s.paused,  # Use paused state from status object
            }
            
            active_downloads[handle_id]['status'] = status_info

            # Check for completed torrents to add to our completed list
            is_finished_or_seeding = s.state == lt.torrent_status.states.seeding or s.state == lt.torrent_status.states.finished
            # 'info' here is the dictionary from active_downloads[handle_id]
            unique_torrent_identifier = info.get('name', handle_id) # Use name if available, else id

            if is_finished_or_seeding and unique_torrent_identifier not in completed_torrents_ids:
                try:
                    ti = handle.torrent_file()
                    if ti:
                        torrent_name = ti.name() if ti.name() else info.get('name', 'Unknown') # Use info here instead of data
                        total_size_bytes = ti.total_size()
                        # Ensure not to add if already present by some other check (though completed_torrents_ids should handle this)
                        if not any(c['id'] == handle_id for c in completed_torrents_info):
                            completed_torrents_info.append({
                                'id': handle_id, 
                                'name': torrent_name,
                                'size': total_size_bytes,
                                'completed_time': time.time() # Store completion time
                            })
                            completed_torrents_ids.add(unique_torrent_identifier)
                            app.logger.info(f"Torrent '{torrent_name}' (ID: {handle_id}) marked as completed and added to completed list.")
                except Exception as e:
                    app.logger.error(f"Error processing completed torrent {handle_id} in update_torrent_status: {e}")
            
        time.sleep(1)

# Start the status update thread
status_thread = Thread(target=update_torrent_status, daemon=True)
status_thread.start()

@app.route('/add_torrent', methods=['POST'])
def add_torrent():
    try:
        magnet_link = request.form.get('magnet_link')
        if not magnet_link or not magnet_link.strip():
            app.logger.error("No magnet link provided in the request")
            return jsonify({'success': False, 'error': 'No magnet link provided'}), 400
            
        save_path = os.path.join(os.path.expanduser("~"), "Downloads", "PythonTorrentDownloader")
        try:
            os.makedirs(save_path, exist_ok=True)
            app.logger.debug(f"Save path set to: {save_path}")
        except Exception as e:
            app.logger.error(f"Failed to create save directory {save_path}: {str(e)}")
            return jsonify({'success': False, 'error': f'Failed to create save directory: {str(e)}'}), 500
        
        app.logger.debug(f"Attempting to add torrent: {magnet_link[:50]}...")
        handle = download_torrent(magnet_link, save_path)
        
        if handle and handle.is_valid():
            handle_id = str(hash(magnet_link))
            
            # Store the magnet link in our list of added magnets if it's not already there
            if magnet_link not in [m['link'] for m in added_magnets]:
                added_magnets.append({
                    'link': magnet_link,
                    'added_at': time.time(),
                    'name': "Fetching metadata...",
                    'handle_id': handle_id
                })
                app.logger.info(f"Added new magnet link to history: {magnet_link[:50]}...")
            
            active_downloads[handle_id] = {
                'handle': handle,
                'status': {},  # Will be populated by update_torrent_status
                'save_path': save_path,
                'name': "Fetching metadata...",  # Initial placeholder name
                'added_at': time.time(),
                'magnet_link': magnet_link
            }
            app.logger.info(f"Successfully added torrent with handle_id: {handle_id}")
            return jsonify({
                'success': True, 
                'handle_id': handle_id,
                'save_path': save_path
            })
        else:
            error_msg = f"Failed to add torrent. Handle is {'invalid' if handle else 'None'}"
            app.logger.error(error_msg)
            return jsonify({'success': False, 'error': error_msg}), 500
            
    except Exception as e:
        error_msg = f"Unexpected error adding torrent: {str(e)}"
        app.logger.error(error_msg, exc_info=True)
        return jsonify({'success': False, 'error': error_msg}), 500
        return jsonify({'success': False, 'error': error_msg}), 500

@app.route('/get_status')
def get_status():
    torrents_status_list = []
    for handle_id, data_dict in active_downloads.items():
        # Start with defaults for all fields expected by the UI
        # 'data_dict' is the value part of active_downloads, e.g., {'handle': ..., 'status': ..., 'name': ...}
        status_defaults = {
            'id': handle_id,
            'name': data_dict.get('name', 'Loading...'), # Use placeholder from add_torrent or a generic one
            'progress': 0.0,
            'download_rate': 0.0,
            'upload_rate': 0.0,
            'state': 'connecting',
            'num_peers': 0,
            'num_seeds': 0,
            'total_download': 0,
            'total_upload': 0,
            'is_paused': False # Assume not paused unless status says otherwise
        }
        
        # Merge with actual status if available, overriding defaults
        actual_status = data_dict.get('status', {})
        merged_status = {**status_defaults, **actual_status}
        
        # Ensure the 'id' is always the correct handle_id from the loop
        merged_status['id'] = handle_id
        
        # Prioritize name from actual_status (if populated by update_torrent_status), 
        # then from data_dict (initial placeholder), then the default.
        if 'name' in actual_status and actual_status.get('name') and actual_status['name'] != "Fetching metadata...":
            merged_status['name'] = actual_status['name']
        elif 'name' in data_dict and data_dict.get('name'):
            merged_status['name'] = data_dict['name']
        # else, it keeps status_defaults['name'] which already used data_dict.get('name', 'Loading...')

        torrents_status_list.append(merged_status)
    return jsonify(torrents_status_list)

# Add these imports at the top
from werkzeug.utils import secure_filename
import humanize

# Add settings endpoint
@app.route('/update_settings', methods=['POST'])
def update_settings():
    data = request.get_json()
    try:
        if 'download_limit' in data:
            download_session.download_rate_limit = int(data['download_limit']) * 1024  # Convert to bytes/s
        if 'upload_limit' in data:
            upload_limit_bytes = int(data['upload_limit']) * 1024
            download_session.upload_rate_limit = upload_limit_bytes
            print(f"Setting UPLOAD rate limit to: {upload_limit_bytes} bytes/s ({data['upload_limit']} KB/s)")
        if 'max_downloads' in data:
            download_session.max_connections = int(data['max_downloads'])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Add torrent details endpoint
@app.route('/torrent_details/<handle_id>')
def torrent_details(handle_id):
    app.logger.debug(f"[Backend] torrent_details: Received request for handle_id: {handle_id}")
    app.logger.debug(f"[Backend] torrent_details: Current active_downloads keys: {list(active_downloads.keys())}")
    if handle_id not in active_downloads:
        app.logger.warning(f"[Backend] torrent_details: handle_id '{handle_id}' not found in active_downloads.")
        return jsonify({
            'error': 'Torrent not found or no longer active',
            'handle_id': handle_id,
            'active_handles': list(active_downloads.keys())
        }), 404

    handle = active_downloads[handle_id]['handle']
    status = handle.status(0) # Pass 0 for default flags
    if not handle.is_valid() or not status.has_metadata:
        return jsonify({'error': 'Metadata not available (handle invalid or no metadata)'})

    torrent_file_ptr = handle.torrent_file()
    if not torrent_file_ptr:
        return jsonify({'error': 'Metadata not available (torrent_file is None)'})

    fs = torrent_file_ptr.files()
    file_progress_list = handle.file_progress() # Keep an eye for similar warnings on this one
    # Replace deprecated handle.file_priorities() with individual calls
    file_priorities_list = [handle.file_priority(idx) for idx in range(fs.num_files())]
    
    files_data = []
    for i in range(fs.num_files()):
        file_path_val = fs.file_path(i)
        file_size_val = fs.file_size(i)
        
        # Ensure path is a string
        path_str = file_path_val.decode('utf-8', errors='ignore') if isinstance(file_path_val, bytes) else file_path_val
        
        progress_val = 0
        if file_size_val > 0 and i < len(file_progress_list):
            # file_progress() returns bytes downloaded for each file
            # To get percentage, it should be (bytes_downloaded / total_size) * 100
            # However, libtorrent's file_progress() when called without piece_granularity might give piece count.
            # For simplicity, if handle.file_progress() returns progress per file directly (0.0 to 1.0), then multiply by 100.
            # Let's assume file_progress_list[i] is bytes downloaded for now.
            # The original code was handle.file_progress()[i] * 100 / file.size - this implies file_progress is not a direct percentage.
            # If file_progress_list[i] is indeed bytes downloaded for file i:
            progress_val = round((file_progress_list[i] / file_size_val) * 100, 2) if file_size_val > 0 else 0
        else:
            # Fallback if file_size is 0 or index out of bounds for progress list
            # Or if the file is fully downloaded based on handle.status().is_seeding or handle.status().is_finished
            if status.is_seeding or (status.is_finished and file_size_val > 0):
                 progress_val = 100.0

        priority_val = 0
        if i < len(file_priorities_list):
            priority_val = file_priorities_list[i]

        files_data.append({
            'index': i,
            'path': path_str,
            'size': file_size_val,
            'progress': progress_val,
            'priority': priority_val
        })

    # Get peer information (keeping this part as is, as no specific deprecation was noted for it)
    peers_data = []
    try:
        peer_info_list = handle.get_peer_info()
        for peer in peer_info_list:
            client_str = peer.client.decode('utf-8', errors='ignore') if isinstance(peer.client, bytes) else peer.client
            peers_data.append({
                'ip': f"{peer.ip[0]}:{peer.ip[1]}",
                'client': client_str,
                'down_speed': round(peer.down_speed / 1024, 2),
                'up_speed': round(peer.up_speed / 1024, 2),
                'progress': round(peer.progress * 100, 2)
            })
    except Exception as e:
        print(f"Error fetching peer info: {e}") # Log error if get_peer_info fails

    return jsonify({
        'files': files_data,
        'peers': peers_data
    })

# Add bulk control endpoint
@app.route('/control_selected', methods=['POST'])
def control_selected():
    data = request.get_json()
    torrents = data.get('torrents', [])
    action = data.get('action')
    
    try:
        for handle_id in torrents:
            if handle_id in active_downloads:
                handle = active_downloads[handle_id]['handle']
                if action == 'pause':
                    print(f"Attempting to PAUSE torrent: {handle_id}")
                    handle.pause()
                    print(f"Torrent {handle_id} paused state after action: {handle.status().is_paused}")
                elif action == 'resume':
                    print(f"Attempting to RESUME torrent: {handle_id}")
                    handle.resume()
                    print(f"Torrent {handle_id} paused state after action: {handle.status().is_paused}")
                elif action == 'delete':
                    handle.remove()
                    del active_downloads[handle_id]
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Add file priority endpoint
@app.route('/set_file_priority/<handle_id>/<int:file_index>/<int:priority>', methods=['POST'])
def set_file_priority(handle_id, file_index, priority):
    if handle_id not in active_downloads:
        return jsonify({'success': False, 'error': 'Torrent not found'})

    handle = active_downloads[handle_id]['handle']
    try:
        handle.file_priority(file_index, priority)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_ip_details', methods=['GET'])
def get_ip_details():
    public_ip_address = get_local_ip() # Fallback or initial value
    location_info = " (Location N/A)"
    try:
        # Query ip-api without specifying an IP to get details for the request's public IP
        # Request 'query' field to get the IP address ip-api.com identified
        response = requests.get('http://ip-api.com/json?fields=status,message,query,country,regionName,city', timeout=5)
        response.raise_for_status() # Raise an exception for HTTP errors
        data = response.json()
        if data.get('status') == 'success':
            public_ip_address = data.get('query', public_ip_address) # Update with IP from API response
            city = data.get('city', '')
            region = data.get('regionName', '')
            country = data.get('country', '')
            location_parts = [part for part in [city, region, country] if part] # Filter out empty parts
            if location_parts:
                location_info = f" ({', '.join(location_parts)})"
    except requests.exceptions.RequestException as e:
        print(f"Error fetching IP location: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while fetching IP location: {e}")
    return jsonify({'ip_address': public_ip_address, 'location': location_info.strip()})

@app.route('/get_current_settings', methods=['GET'])
def get_current_settings():
    # Get current settings pack from the session
    current_libtorrent_settings = download_session.get_settings()

    # Fetch rate limits from settings
    # In newer versions of libtorrent, settings are accessed directly as dictionary keys
    dl_rate_val = current_libtorrent_settings.get('download_rate_limit', 0)
    ul_rate_val = current_libtorrent_settings.get('upload_rate_limit', 0)

    # Get max parallel downloads (active_downloads_limit)
    max_parallel_downloads_val = current_libtorrent_settings.get('active_downloads_limit', 20)  # Default to 20 if not set

    app.logger.debug(f"Current download_rate_limit from session: {dl_rate_val} bytes/s")
    app.logger.debug(f"Current upload_rate_limit from session: {ul_rate_val} bytes/s")
    app.logger.debug(f"Current active_downloads_limit from session: {max_parallel_downloads_val}")

    # Convert rates to KB/s for display. If rate is <= 0 (i.e., 0 or -1 for unlimited), display as 0 KB/s.
    download_limit_kb = (dl_rate_val // 1024) if dl_rate_val > 0 else 0
    upload_limit_kb = (ul_rate_val // 1024) if ul_rate_val > 0 else 0
    
    # max_parallel_downloads_val is the direct integer value.
    return jsonify({
        'download_limit': download_limit_kb,
        'upload_limit': upload_limit_kb,
        'max_downloads': max_parallel_downloads_val
    })

@app.route('/start_all_torrents', methods=['POST'])
def start_all_torrents():
    app.logger.info("Attempting to start all torrents (resume all paused).")
    resumed_count = 0
    if not active_downloads:
        app.logger.info("No active torrents to start.")
        return jsonify({'success': True, 'message': 'No active torrents to start.', 'resumed_count': resumed_count})
    
    for torrent_id, data in list(active_downloads.items()): # Iterate over a copy for safe modification
        handle = data.get('handle')
        if handle and handle.is_valid():
            try:
                status = handle.status(0) # Get current status
                if status.paused:
                    handle.resume()
                    app.logger.info(f"Resumed torrent: {status.name if status.has_metadata else 'N/A'} (ID: {torrent_id})")
                    resumed_count += 1
                # else: app.logger.info(f"Torrent already running or not paused: {status.name if status.has_metadata else 'N/A'} (ID: {torrent_id})")
            except Exception as e:
                app.logger.error(f"Error resuming torrent {torrent_id}: {e}")
    app.logger.info(f"Finished attempting to start all torrents. Resumed: {resumed_count}")
    return jsonify({'success': True, 'message': f'Attempted to resume all paused torrents. Resumed {resumed_count} torrent(s).', 'resumed_count': resumed_count})

@app.route('/pause_all_torrents', methods=['POST'])
def pause_all_torrents():
    app.logger.info("Attempting to pause all active torrents.")
    paused_count = 0
    if not active_downloads:
        app.logger.info("No active torrents to pause.")
        return jsonify({'success': True, 'message': 'No active torrents to pause.', 'paused_count': paused_count})

    for torrent_id, data in list(active_downloads.items()): # Iterate over a copy
        handle = data.get('handle')
        if handle and handle.is_valid():
            try:
                status = handle.status(0) # Get current status
                if not status.paused:
                    handle.pause()
                    app.logger.info(f"Paused torrent: {status.name if status.has_metadata else 'N/A'} (ID: {torrent_id})")
                    paused_count += 1
                # else: app.logger.info(f"Torrent already paused: {status.name if status.has_metadata else 'N/A'} (ID: {torrent_id})")
            except Exception as e:
                app.logger.error(f"Error pausing torrent {torrent_id}: {e}")
    app.logger.info(f"Finished attempting to pause all torrents. Paused: {paused_count}")
    return jsonify({'success': True, 'message': f'Attempted to pause all active torrents. Paused {paused_count} torrent(s).', 'paused_count': paused_count})

@app.route('/set_no_upload', methods=['POST'])
def set_no_upload():
    try:
        download_session.upload_rate_limit = 0 # 0 means no limit, but effectively stops if no one is downloading from you or for specific interpretations.
                                               # More robustly, for libtorrent, setting to 1 might be 'minimal'. Let's use 0 for now as per typical UI understanding.
        app.logger.info(f"Global upload rate limit set to 0 KB/s.")
        # Persist this as a setting if your settings persistence logic was more advanced
        # For now, it's a session-level change.
        return jsonify({'success': True, 'message': 'Upload speed limit set to 0 KB/s.'})
    except Exception as e:
        app.logger.error(f"Error setting no upload: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/stop_all_torrents', methods=['POST'])
def stop_all_torrents():
    global active_downloads
    stopped_count = 0
    torrents_to_remove = list(active_downloads.keys()) # Iterate over a copy of keys

    for handle_id in torrents_to_remove:
        if handle_id in active_downloads:
            handle_info = active_downloads[handle_id]
            handle = handle_info['handle']
            try:
                if handle.is_valid() and not handle.status(0).is_paused:
                    handle.pause()
                    app.logger.info(f"Paused torrent {handle_id} before stopping.")
                # Wait a moment for pause to take effect if necessary, though libtorrent is usually quick
                # Remove from session (this doesn't delete files, just stops tracking)
                if download_session and handle.is_valid(): # Check if session is available
                    download_session.remove_torrent(handle, lt.options_t.delete_files if handle_info.get('delete_files_on_stop', False) else 0)
                
                del active_downloads[handle_id]
                stopped_count += 1
                app.logger.info(f"Stopped and removed torrent {handle_id}.")
            except Exception as e:
                app.logger.error(f"Error stopping torrent {handle_id}: {e}")
        else:
            app.logger.warning(f"Torrent {handle_id} not found in active_downloads during stop_all operation.")

    app.logger.info(f"Finished attempting to stop all torrents. Stopped: {stopped_count}")
    return jsonify({'success': True, 'message': f'Attempted to stop all torrents. Stopped and removed {stopped_count} torrent(s).', 'stopped_count': stopped_count})

@app.route('/get_completed_torrents')
def get_completed_torrents_route():
    # Sort by completion time, newest first, if desired
    # sorted_completed = sorted(completed_torrents_info, key=lambda x: x.get('completed_time', 0), reverse=True)
    return jsonify(completed_torrents_info)

@app.route('/get_added_magnets')
def get_added_magnets_route():
    # Sort by addition time, newest first
    sorted_magnets = sorted(added_magnets, key=lambda x: x.get('added_at', 0), reverse=True)
    return jsonify(sorted_magnets)

@app.route('/open_folder')
def open_folder():
    """Open the specified folder in the system file explorer."""
    path = request.args.get('path')
    if not path:
        return jsonify({'success': False, 'error': 'No path provided'}), 400
    
    try:
        # Normalize the path and ensure it exists
        path = os.path.normpath(path)
        if not os.path.exists(path):
            return jsonify({'success': False, 'error': 'Path does not exist'}), 404
            
        # Use the appropriate command based on the operating system
        if os.name == 'nt':  # Windows
            os.startfile(path)
        elif os.name == 'posix':  # macOS and Linux
            if sys.platform == 'darwin':  # macOS
                subprocess.run(['open', path], check=True)
            else:  # Linux
                subprocess.run(['xdg-open', path], check=True)
        else:
            return jsonify({'success': False, 'error': 'Unsupported operating system'}), 501
            
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f'Error opening folder {path}: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # Ensure local_ip is updated before running, in case get_local_ip() behavior changes
    local_ip = get_local_ip()
    print(f"Serving on http://{local_ip}:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)