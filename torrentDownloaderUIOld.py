import libtorrent as lt
import time
import os
import threading
import queue
from flask import Flask, render_template, request, jsonify
import json
import atexit # Import atexit for proper shutdown

# --- Flask App Initialization ---\
app = Flask(__name__)

# --- Libtorrent Global Objects ---
torrent_session = None
torrent_handles = {}  # Dictionary to store active torrent handles: {info_hash: handle}
libtorrent_command_queue = queue.Queue()
libtorrent_status_lock = threading.Lock()
stop_event = threading.Event()

global_download_limit = 0
global_upload_limit = 0

# --- Libtorrent Thread Worker Function ---
def libtorrent_thread_worker():
    global torrent_session, global_download_limit, global_upload_limit

    torrent_session = lt.session()
    torrent_session.listen_on(6881, 6891)
    # Set all alert categories for comprehensive logging during debugging
    torrent_session.set_alert_mask(lt.alert.category_t.all_categories) # <--- ADDED FOR DEBUGGING

    print("Libtorrent session started in background thread.")

    torrent_session.set_download_rate_limit(global_download_limit)
    torrent_session.set_upload_rate_limit(global_upload_limit)

    while not stop_event.is_set():
        try:
            command = libtorrent_command_queue.get(timeout=0.1)
            action = command.get("action")
            data = command.get("data")

            if action == "add":
                link = data["link"]
                print(f"Received magnet link: {link}")
                
                try:
                    atp = lt.parse_magnet_uri(link) 

                    atp.save_path = DOWNLOAD_PATH
                    atp.storage_mode = lt.storage_mode_t.storage_mode_sparse
                    atp.flags |= lt.torrent_flags.auto_managed 

                    handle = torrent_session.add_torrent(atp) 

                    with libtorrent_status_lock:
                        torrent_handles[str(handle.info_hash())] = handle
                    print(f"Added magnet link via UI: {link}")
                except Exception as e:
                    print(f"Error adding torrent: {e}")
            # ... (rest of add/toggle/remove actions)

        except queue.Empty:
            pass

        # Process libtorrent alerts
        torrent_session.wait_for_alert(100) # milliseconds
        alerts = torrent_session.pop_alerts()
        for a in alerts:
            print(f"LIBTORRENT ALERT: {a.what()} - {a.message()}")

            if a.category() & lt.alert.category_t.storage_notification:
                if isinstance(a, lt.torrent_finished_alert):
                    with libtorrent_status_lock:
                        handle = a.handle
                        if handle.is_valid():
                            info_hash_str = str(handle.info_hash())
                            # FIX: Use a.torrent_name directly as it's an attribute, not a method
                            print(f"Torrent '{a.torrent_name}' finished!") 
                            # You might want to update status for UI, e.g., mark as 'finished'

            # Additional alerts for debugging torrent state, errors, and metadata
            if isinstance(a, lt.add_torrent_alert):
                # FIX: Use a.torrent_name directly
                print(f"LIBTORRENT ADD TORRENT ALERT: Torrent '{a.torrent_name}' added successfully. Info Hash: {a.handle.info_hash()}")
            elif isinstance(a, lt.torrent_error_alert):
                # FIX: Use a.torrent_name directly
                print(f"LIBTORRENT TORRENT ERROR: Torrent '{a.torrent_name}' (Info Hash: {a.handle.info_hash()}) Error: {a.message()}")
            elif isinstance(a, lt.tracker_error_alert):
                # FIX: Use a.torrent_name directly
                print(f"LIBTORRENT TRACKER ERROR: Torrent '{a.torrent_name}' Tracker: {a.tracker_url()} Error: {a.message()}")
            elif isinstance(a, lt.peer_connect_alert):
                # FIX: Use a.torrent_name directly
                print(f"LIBTORRENT PEER CONNECT: {a.endpoint()} for {a.torrent_name}")
            elif isinstance(a, lt.peer_disconnected_alert):
                # FIX: Use a.torrent_name directly
                print(f"LIBTORRENT PEER DISCONNECT: {a.endpoint()} for {a.torrent_name} - Reason: {a.error.message()}")
            elif isinstance(a, lt.portmap_alert):
                print(f"LIBTORRENT PORTMAP: {a.name()} - External port: {a.external_port}")
            elif isinstance(a, lt.metadata_received_alert):
                # FIX: Use a.torrent_name directly
                print(f"LIBTORRENT METADATA RECEIVED: Torrent '{a.torrent_name}' for {a.handle.info_hash()}")

    print("Libtorrent thread shutting down.")
    torrent_session = None

# ... (rest of the Flask routes)

# ... (Your existing global definitions, including the global state_str) ...

state_str = ['queued', 'checking', 'downloading metadata', \
             'downloading', 'finished', 'seeding', 'allocating', 'checking resume data'] # <--- Keep this GLOBAL definition


@app.route('/status')
def get_status():
    status_list = []
    with libtorrent_status_lock:
        for info_hash, handle in list(torrent_handles.items()):
            if not handle.is_valid():
                print(f"Cleaning up invalid handle: {info_hash}")
                del torrent_handles[info_hash]
                continue

            s = handle.status()

            # Debugging log for each torrent's full status
            # This line will now correctly use the global state_str
            print(f"DEBUG STATUS for {info_hash}: "
                #   f"State={state_str[s.state]}, "
                  f"Progress={s.progress*100:.2f}%, "
                  f"DL Rate={s.download_rate / 1000:.2f}KB/s, "
                  f"UP Rate={s.upload_rate / 1000:.2f}KB/s, "
                  f"Peers={s.num_peers}, "
                  f"ETA={s.eta}s, "
                  f"Total Downloaded={s.total_download / (1024*1024):.2f}MB, "
                  f"Total Uploaded={s.total_upload / (1024*1024):.2f}MB, "
                  f"Metadata={s.has_metadata}, "
                  f"Error={s.error}")

            torrent_name = ""
            if s.has_metadata:
                try:
                    torrent_info = handle.torrent_file()
                    torrent_name = torrent_info.name()
                except Exception as e:
                    print(f"Error getting torrent_file() name for {info_hash}: {e}")
                    torrent_name = s.name if s.name else info_hash[:10] + "..."
            else:
                torrent_name = f"Fetching metadata ({s.progress*100:.2f}%)"

            # --- REMOVE THIS BLOCK ---
            # You currently have this duplicate definition inside get_status
            # state_str = ['queued', 'checking', 'downloading metadata', \
            #              'downloading', 'finished', 'seeding', 'allocating', 'checking resume data']
            # --- END REMOVE BLOCK ---

            eta_seconds = s.eta
            eta_display = "N/A"
            if eta_seconds > 0 and eta_seconds != lt.i2p_stream_flags.i2p_no_progress and s.state == lt.torrent_status.downloading:
                mins, secs = divmod(int(eta_seconds), 60)
                hours, mins = divmod(mins, 60)
                if hours > 0:
                    eta_display = f"{hours}h {mins}m {secs}s"
                elif mins > 0:
                    eta_display = f"{mins}m {secs}s"
                else:
                    eta_display = f"{secs}s"
            elif s.is_finished:
                eta_display = "Done"

            status_list.append({
                "info_hash": info_hash,
                "name": torrent_name,
                "progress": s.progress * 100,
                "download_rate": s.download_rate / 1000, # kB/s
                "upload_rate": s.upload_rate / 1000,     # kB/s
                "num_peers": s.num_peers,
                "state": state_str[s.state],
                "eta": eta_display,
                "total_downloaded": s.total_download / (1024*1024), # MB
                "total_uploaded": s.total_upload / (1024*1024),     # MB
                "total_size": (handle.torrent_file().total_size() / (1024*1024)) if s.has_metadata else 0 # MB
            })
    return jsonify(status_list)

# ... (The rest of your file) ...
    status_list = []
    with libtorrent_status_lock:
        for info_hash, handle in list(torrent_handles.items()):
            if not handle.is_valid():
                print(f"Cleaning up invalid handle: {info_hash}")
                del torrent_handles[info_hash]
                continue

            s = handle.status()

            # Debugging log for each torrent's full status
            # FIX: Change s.time_remaining to s.eta
            print(f"DEBUG STATUS for {info_hash}: "
                  f"State={state_str[s.state]}, "
                  f"Progress={s.progress*100:.2f}%, "
                  f"DL Rate={s.download_rate / 1000:.2f}KB/s, "
                  f"UP Rate={s.upload_rate / 1000:.2f}KB/s, "
                  f"Peers={s.num_peers}, "
                  f"ETA={s.eta}s, " # FIX: Use s.eta
                  f"Total Downloaded={s.total_download / (1024*1024):.2f}MB, "
                  f"Total Uploaded={s.total_upload / (1024*1024):.2f}MB, "
                  f"Metadata={s.has_metadata}, "
                  f"Error={s.error}")

            torrent_name = ""
            if s.has_metadata:
                try:
                    torrent_info = handle.torrent_file()
                    torrent_name = torrent_info.name()
                except Exception as e:
                    print(f"Error getting torrent_file() name for {info_hash}: {e}")
                    torrent_name = s.name if s.name else info_hash[:10] + "..."
            else:
                torrent_name = f"Fetching metadata ({s.progress*100:.2f}%)"

            state_str = ['queued', 'checking', 'downloading metadata', \
                         'downloading', 'finished', 'seeding', 'allocating', 'checking resume data']

            # FIX: Change s.time_remaining to s.eta
            eta_seconds = s.eta 
            eta_display = "N/A"
            # FIX: The condition for eta_seconds > 0 should ideally also check if s.eta is not lt.torrent_status.kNoProgress
            if eta_seconds > 0 and eta_seconds != lt.i2p_stream_flags.i2p_no_progress and s.state == lt.torrent_status.downloading: # Added check for kNoProgress/i2p_no_progress as a common constant for 'no ETA'
                mins, secs = divmod(int(eta_seconds), 60)
                hours, mins = divmod(mins, 60)
                if hours > 0:
                    eta_display = f"{hours}h {mins}m {secs}s"
                elif mins > 0:
                    eta_display = f"{mins}m {secs}s"
                else:
                    eta_display = f"{secs}s"
            elif s.is_finished:
                eta_display = "Done"

            status_list.append({
                "info_hash": info_hash,
                "name": torrent_name,
                "progress": s.progress * 100,
                "download_rate": s.download_rate / 1000, # kB/s
                "upload_rate": s.upload_rate / 1000,     # kB/s
                "num_peers": s.num_peers,
                "state": state_str[s.state],
                "eta": eta_display,
                "total_downloaded": s.total_download / (1024*1024), # MB
                "total_uploaded": s.total_upload / (1024*1024),     # MB
                "total_size": (handle.torrent_file().total_size() / (1024*1024)) if s.has_metadata else 0 # MB
            })
    return jsonify(status_list)

# ... (rest of the file, including the __name__ == '__main__': block)
# --- Flask Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_torrent', methods=['POST'])
def add_torrent_route():
    data = request.get_json()
    magnet_link = data.get('magnet_link')
    print("In add_torrent_route") # Debug print
    if magnet_link:
        libtorrent_command_queue.put({"action": "add", "data": {"link": magnet_link}})
        return jsonify({"status": "success", "message": "Torrent add command queued."})
    return jsonify({"status": "error", "message": "No magnet link provided."}), 400

@app.route('/toggle_torrent', methods=['POST'])
def toggle_torrent_route():
    data = request.get_json()
    info_hash = data.get('info_hash')
    if info_hash:
        libtorrent_command_queue.put({"action": "toggle_state", "data": {"info_hash": info_hash}})
        return jsonify({"status": "success", "message": "Torrent state toggle command queued."})
    return jsonify({"status": "error", "message": "No info hash provided."}), 400

@app.route('/remove_torrent', methods=['POST'])
def remove_torrent_route():
    data = request.get_json()
    info_hash = data.get('info_hash')
    if info_hash:
        libtorrent_command_queue.put({"action": "remove", "data": {"info_hash": info_hash}})
        return jsonify({"status": "success", "message": "Torrent remove command queued."})
    return jsonify({"status": "error", "message": "No info hash provided."}), 400


# ... (near the top of your script, with other global variables) ...

state_str = ['queued', 'checking', 'downloading metadata', \
             'downloading', 'finished', 'seeding', 'allocating', 'checking resume data']

# ... (rest of your code) ...

# @app.route('/status')
# def get_status():
#     status_list = []
#     with libtorrent_status_lock:
#         for info_hash, handle in list(torrent_handles.items()): # Use list() to iterate over a copy
#             if not handle.is_valid():
#                 print(f"Cleaning up invalid handle: {info_hash}")
#                 del torrent_handles[info_hash]
#                 continue

#             s = handle.status()

#             # Debugging log for each torrent's full status
#             print(f"DEBUG STATUS for {info_hash}: "
#                   f"State={state_str[s.state]}, "
#                   f"Progress={s.progress*100:.2f}%, "
#                   f"DL Rate={s.download_rate / 1000:.2f}KB/s, "
#                   f"UP Rate={s.upload_rate / 1000:.2f}KB/s, "
#                   f"Peers={s.num_peers}, "
#                   f"ETA={s.time_remaining}s, "
#                   f"Total Downloaded={s.total_download / (1024*1024):.2f}MB, "
#                   f"Total Uploaded={s.total_upload / (1024*1024):.2f}MB, "
#                   f"Metadata={s.has_metadata}, "
#                   f"Error={s.error}") # Check for s.error

#             torrent_name = ""
#             if s.has_metadata:
#                 try:
#                     torrent_info = handle.torrent_file()
#                     torrent_name = torrent_info.name()
#                 except Exception as e:
#                     print(f"Error getting torrent_file() name for {info_hash}: {e}")
#                     torrent_name = s.name if s.name else info_hash[:10] + "..."
#             else:
#                 torrent_name = f"Fetching metadata ({s.progress*100:.2f}%)"


#             eta_seconds = s.time_remaining
#             eta_display = "N/A"
#             if eta_seconds > 0 and s.state == lt.torrent_status.downloading:
#                 mins, secs = divmod(int(eta_seconds), 60)
#                 hours, mins = divmod(mins, 60)
#                 if hours > 0:
#                     eta_display = f"{hours}h {mins}m {secs}s"
#                 elif mins > 0:
#                     eta_display = f"{mins}m {secs}s"
#                 else:
#                     eta_display = f"{secs}s"
#             elif s.is_finished:
#                 eta_display = "Done"

#             status_list.append({
#                 "info_hash": info_hash,
#                 "name": torrent_name,
#                 "progress": s.progress * 100,
#                 "download_rate": s.download_rate / 1000, # kB/s
#                 "upload_rate": s.upload_rate / 1000,     # kB/s
#                 "num_peers": s.num_peers,
#                 "state": state_str[s.state],
#                 "eta": eta_display,
#                 "total_downloaded": s.total_download / (1024*1024), # MB
#                 "total_uploaded": s.total_upload / (1024*1024),     # MB
#                 "total_size": (handle.torrent_file().total_size() / (1024*1024)) if s.has_metadata else 0 # MB
#             })
#     return jsonify(status_list)

@app.route('/set_speed_limits', methods=['POST'])
def set_speed_limits_route():
    data = request.get_json()
    dl_limit_kb = data.get('download_limit_kb', 0)
    ul_limit_kb = data.get('upload_limit_kb', 0)

    # Convert KB/s to bytes/second for libtorrent
    dl_limit_bytes = dl_limit_kb * 1024
    ul_limit_bytes = ul_limit_kb * 1024

    libtorrent_command_queue.put({
        "action": "set_global_limits",
        "data": {
            "download_limit": dl_limit_bytes,
            "upload_limit": ul_limit_bytes
        }
    })
    return jsonify({"status": "success", "message": "Speed limits updated."})


# --- Flask App Lifecycle Hooks ---
# REMOVED @app.before_request and @app.teardown_appcontext for libtorrent thread management
# Thread management should be done once on app startup/shutdown

# Define a global thread variable
libtorrent_thread = None

def start_libtorrent_thread_once():
    """Starts the libtorrent worker thread once."""
    global libtorrent_thread
    if libtorrent_thread is None or not libtorrent_thread.is_alive():
        libtorrent_thread = threading.Thread(target=libtorrent_thread_worker, daemon=True)
        libtorrent_thread.start()
        print("Libtorrent worker thread started.")

def shutdown_libtorrent_thread_once():
    """Signals the libtorrent worker thread to stop when the app shuts down."""
    global libtorrent_thread
    if libtorrent_thread and libtorrent_thread.is_alive():
        print("Signaling libtorrent thread to stop...")
        stop_event.set()
        libtorrent_thread.join(timeout=5) # Give the thread some time to clean up
        if libtorrent_thread.is_alive():
            print("Libtorrent thread did not terminate gracefully.")

if __name__ == '__main__':
    # --- Configuration ---
    DOWNLOAD_PATH = r"C:\Users\STK911\Downloads\PythonTorrentDownloader"
    os.makedirs(DOWNLOAD_PATH, exist_ok=True)
    print(f"Download path set to: {DOWNLOAD_PATH}") # Confirm path

    # Start the libtorrent thread once when the application starts
    start_libtorrent_thread_once()

    # Register the shutdown function to be called when the Python interpreter exits
    atexit.register(shutdown_libtorrent_thread_once)

    app.run(debug=True, port=5000, use_reloader=False) # use_reloader=False is important
                                                       # to prevent thread from starting twice
                                                       # with Flask's reloader