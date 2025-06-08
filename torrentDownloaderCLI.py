import libtorrent as lt
import time
import os

def download_torrent(ses, magnet_link_or_file_path, save_path="."):
    """
    Downloads a torrent from a magnet link or a .torrent file using an existing libtorrent session.

    Args:
        ses (libtorrent.session): The active libtorrent session.
        magnet_link_or_file_path (str): The magnet link or the path to the .torrent file.
        save_path (str): The directory where the downloaded files will be saved.
                         Defaults to the current directory ('.').
    """

    # Create parameters for adding the torrent
    params = {
        'save_path': save_path,
        'storage_mode': lt.storage_mode_t.storage_mode_sparse, # Only allocate space as needed
    }

    # Add the torrent to the session
    try:
        if magnet_link_or_file_path.startswith("magnet:?"):
            print(f"Adding magnet link: {magnet_link_or_file_path}")
            handle = lt.add_magnet_uri(ses, magnet_link_or_file_path, params)
        elif os.path.exists(magnet_link_or_file_path) and magnet_link_or_file_path.endswith(".torrent"):
            print(f"Loading .torrent file: {magnet_link_or_file_path}")
            # Load the .torrent file as a torrent_info object
            ti = lt.torrent_info(magnet_link_or_file_path)
            handle = ses.add_torrent({'ti': ti, 'save_path': save_path})
        else:
            print("Invalid input. Please provide a valid magnet link or a path to a .torrent file.")
            return None # Return None if input is invalid

        print(f"Torrent added. Waiting for metadata (if magnet link).")

        # Wait for torrent metadata to be downloaded (only for magnet links)
        # For parallel downloads, we can't block here for metadata.
        # Metadata will be fetched in the main download loop.
        # However, for initial setup, we should ensure metadata is fetched for each torrent
        # before starting the main loop if we want accurate torrent names from the start.
        # For simplicity in parallel monitoring, we will rely on the main loop.

        return handle # Return the handle to be managed by the main loop

    except Exception as e:
        print(f"An error occurred while adding torrent: {e}")
        return None


if __name__ == "__main__":
    # --- Configuration ---
    DOWNLOAD_PATH = r"C:\Users\STK911\Downloads\PythonTorrentDownloader"
    # Ensure the download directory exists
    os.makedirs(DOWNLOAD_PATH, exist_ok=True)
    print(f"Downloads will be saved to: {os.path.abspath(DOWNLOAD_PATH)}")

    # List of magnet links to download in parallel
    magnet_links = [
        "magnet:?xt=urn:btih:1735b2a5ce5c3eeb8bdedbe53145237e0473f517&dn=www.5MovieRulz.frl%20-%20Housefull%205A%20(2025)%201080p%20Hindi%20DVDScr%20-%20x264%20-%20AAC%20-%202.9GB.mkv&tr=udp%3a%2f%2ftracker.opentrackr.org%3a1337%2fannounce&tr=udp%3a%2f%2fopen.demonii.com%3a1337%2fannounce&tr=udp%3a%2f%2fopen.tracker.cl%3a1337%2fannounce&tr=udp%3a%2f%2fopen.stealth.si%3a80%2fannounce&tr=udp%3a%2f%2ftracker.torrent.eu.org%3a451%2fannounce&tr=udp%3a%2f%2ftracker.ololosh.space%3a6969%2fannounce&tr=udp%3a%2f%2ftracker.dump.cl%3a6969%2fannounce&tr=udp%3a%2f%2ftracker.bittor.pw%3a1337%2fannounce&tr=udp%3a%2f%2fopentracker.io%3a6969%2fannounce&tr=udp%3a%2f%2fisk.richardsw.club%3a6969%2fannounce&tr=udp%3a%2f%2fdiscord.heihachi.pw%3a6969%2fannounce&tr=http%3a%2f%2fwww.torrentsnipe.info%3a2701%2fannounce&tr=http%3a%2f%2ftracker810.xyz%3a11450%2fannounce&tr=http%3a%2f%2ftracker.vanitycore.co%3a6969%2fannounce&tr=http%3a%2f%2ftracker.sbsub.com%3a2710%2fannounce&tr=http%3a%2f%2ftracker.moxing.party%3a6969%2fannounce&tr=http%3a%2f%2ftracker.lintk.me%3a2710%2fannounce",
        "magnet:?xt=urn:btih:f1428a477f91d3ec90e4088a13ffd82b1d9feaaf&dn=www.5MovieRulz.frl%20-%20Jora%20Kaiya%20Thattunga%20(2025)%201080p%20Tamil%20TRUE%20WEB-DL%20-%20AVC%20-%20(DD%2b5.1%20-%20640Kbps%20%26%20AAC)%20-%202.3GB%20-%20ESub.mkv&tr=udp%3a%2f%2ftracker.opentrackr.org%3a1337%2fannounce&tr=udp%3a%2f%2fopen.demonii.com%3a1337%2fannounce&tr=udp%3a%2f%2fopen.tracker.cl%3a1337%2fannounce&tr=udp%3a%2f%2fopen.stealth.si%3a80%2fannounce&tr=udp%3a%2f%2ftracker.torrent.eu.org%3a451%2fannounce&tr=udp%3a%2f%2ftracker.ololosh.space%3a6969%2fannounce&tr=udp%3a%2f%2ftracker.dump.cl%3a6969%2fannounce&tr=udp%3a%2f%2ftracker.bittor.pw%3a1337%2fannounce&tr=udp%3a%2f%2fopentracker.io%3a6969%2fannounce&tr=udp%3a%2f%2fisk.richardsw.club%3a6969%2fannounce&tr=udp%3a%2f%2fdiscord.heihachi.pw%3a6969%2fannounce&tr=http%3a%2f%2fwww.torrentsnipe.info%3a2701%2fannounce&tr=http%3a%2f%2ftracker810.xyz%3a11450%2fannounce&tr=http%3a%2f%2ftracker.vanitycore.co%3a6969%2fannounce&tr=http%3a%2f%2ftracker.sbsub.com%3a2710%2fannounce&tr=http%3a%2f%2ftracker.moxing.party%3a6969%2fannounce&tr=http%3a%2f%2ftracker.lintk.me%3a2710%2fannounce",
        "magnet:?xt=urn:btih:04dd2d83b39763c68ee97600c42782217189002c&dn=K.O.%20(2025)%201080p%20HQ%20HDRip%20%20-%20x264%20-%20(DD%2b%205.1%20-%20640kbps)%20%5bTel%20%2b%20Tam%20%2b%20Hin%20%2b%20Eng%5d.mkv&tr=udp%3a%2f%2ftracker.opentrackr.org%3a1337%2fannounce&tr=udp%3a%2f%2fopen.demonii.com%3a1337%2fannounce&tr=udp%3a%2f%2fopen.tracker.cl%3a1337%2fannounce&tr=udp%3a%2f%2fopen.stealth.si%3a80%2fannounce&tr=udp%3a%2f%2ftracker.torrent.eu.org%3a451%2fannounce&tr=udp%3a%2f%2ftracker.ololosh.space%3a6969%2fannounce&tr=udp%3a%2f%2ftracker.dump.cl%3a6969%2fannounce&tr=udp%3a%2f%2ftracker.bittor.pw%3a1337%2fannounce&tr=udp%3a%2f%2fopentracker.io%3a6969%2fannounce&tr=udp%3a%2f%2fisk.richardsw.club%3a6969%2fannounce&tr=udp%3a%2f%2fdiscord.heihachi.pw%3a6969%2fannounce&tr=http%3a%2f%2fwww.torrentsnipe.info%3a2701%2fannounce&tr=http%3a%2f%2ftracker810.xyz%3a11450%2fannounce&tr=http%3a%2f%2ftracker.vanitycore.co%3a6969%2fannounce&tr=http%3a%2f%2ftracker.sbsub.com%3a2710%2fannounce&tr=http%3a%2f%2ftracker.moxing.party%3a6969%2fannounce&tr=http%3a%2f%2ftracker.lintk.me%3a2710%2fannounce",
        "magnet:?xt=urn:btih:5050d096cba8e5f64c8483d0e140c6e78f4043a2&dn=The%20Last%20Wish%20(2025)%201080p%20HQ%20HDRip%20-%20x264%20-%20%5bTel%20%2b%20Tam%20%2b%20Hin%20%2b%20Tur%5d.mkv&tr=udp%3a%2f%2ftracker.opentrackr.org%3a1337%2fannounce&tr=udp%3a%2f%2fopen.demonii.com%3a1337%2fannounce&tr=udp%3a%2f%2fopen.tracker.cl%3a1337%2fannounce&tr=udp%3a%2f%2fopen.stealth.si%3a80%2fannounce&tr=udp%3a%2f%2ftracker.torrent.eu.org%3a451%2fannounce&tr=udp%3a%2f%2ftracker.ololosh.space%3a6969%2fannounce&tr=udp%3a%2f%2ftracker.dump.cl%3a6969%2fannounce&tr=udp%3a%2f%2ftracker.bittor.pw%3a1337%2fannounce&tr=udp%3a%2f%2fopentracker.io%3a6969%2fannounce&tr=udp%3a%2f%2fisk.richardsw.club%3a6969%2fannounce&tr=udp%3a%2f%2fdiscord.heihachi.pw%3a6969%2fannounce&tr=http%3a%2f%2fwww.torrentsnipe.info%3a2701%2fannounce&tr=http%3a%2f%2ftracker810.xyz%3a11450%2fannounce&tr=http%3a%2f%2ftracker.vanitycore.co%3a6969%2fannounce&tr=http%3a%2f%2ftracker.sbsub.com%3a2710%2fannounce&tr=http%3a%2f%2ftracker.moxing.party%3a6969%2fannounce&tr=http%3a%2f%2ftracker.lintk.me%3a2710%2fannounce",
        "magnet:?xt=urn:btih:784c6196f7871af3418d29a6faf9790eabe35a74&dn=www.5MovieRulz.realty%20-%20Devika%20%26%20Danny%20(2025)%201080p%20S01%20EP%20(01-07)%20TRUE%20WEB-DL%20-%20AVC%20-%20%5bTel%20%2b%20Tam%2b%20Hin%20%2b%20Mal%20%2b%2b%20Kan%5d&tr=udp%3a%2f%2ftracker.opentrackr.org%3a1337%2fannounce&tr=udp%3a%2f%2fopen.demonii.com%3a1337%2fannounce&tr=udp%3a%2f%2fopen.tracker.cl%3a1337%2fannounce&tr=udp%3a%2f%2fopen.stealth.si%3a80%2fannounce&tr=udp%3a%2f%2ftracker.torrent.eu.org%3a451%2fannounce&tr=udp%3a%2f%2ftracker.ololosh.space%3a6969%2fannounce&tr=udp%3a%2f%2ftracker.dump.cl%3a6969%2fannounce&tr=udp%3a%2f%2ftracker.bittor.pw%3a1337%2fannounce&tr=udp%3a%2f%2fopentracker.io%3a6969%2fannounce&tr=udp%3a%2f%2fisk.richardsw.club%3a6969%2fannounce&tr=udp%3a%2f%2fdiscord.heihachi.pw%3a6969%2fannounce&tr=http%3a%2f%2fwww.torrentsnipe.info%3a2701%2fannounce&tr=http%3a%2f%2ftracker810.xyz%3a11450%2fannounce&tr=http%3a%2f%2ftracker.vanitycore.co%3a6969%2fannounce&tr=http%3a%2f%2ftracker.sbsub.com%3a2710%2fannounce&tr=http%3a%2f%2ftracker.moxing.party%3a6969%2fannounce&tr=http%3a%2f%2ftracker.lintk.me%3a2710%2fannounce"
        # Add more magnet links here
    ]

    # Initialize a single libtorrent session for all downloads
    ses = lt.session()
    ses.listen_on(6881, 6891)
    print(f"Torrent session initialized. Listening on ports 6881-6891.")

    # List to hold all torrent handles
    handles = []
    for link in magnet_links:
        # Pass the single session object to the download_torrent function
        handle = download_torrent(ses, link, save_path=DOWNLOAD_PATH)
        if handle:
            handles.append(handle)

    if not handles:
        print("No valid torrents to download. Exiting.")
    else:
        print(f"\n--- Starting parallel download of {len(handles)} torrents ---")
        active_downloads = len(handles)
        state_str = ['queued', 'checking', 'downloading metadata', \
                'downloading', 'finished', 'seeding', 'allocating', 'checking fastresume']

        while active_downloads > 0:
            active_downloads = 0
            for i, handle in enumerate(handles):
                s = handle.status()

                # Check if torrent has finished
                if s.is_finished:
                    if not getattr(handle, '_finished_printed', False): # Use a flag to print only once
                        print(f"\n[{i+1}/{len(handles)}] Torrent '{s.name}' finished successfully! Saved to: {os.path.abspath(DOWNLOAD_PATH)}")
                        handle._finished_printed = True # Set the flag
                    # Continue seeding, but don't count as 'active downloading'
                    if s.state != lt.torrent_status.seeding:
                        # Only count as 'finished' if it's explicitly finished and not yet seeding
                        pass # Don't decrement active_downloads until truly done
                    else:
                        active_downloads += 1 # Count as active if seeding
                elif s.error: # Corrected: Check if s.error string is not empty
                    if not getattr(handle, '_error_printed', False): # Use a flag
                        print(f"\n[{i+1}/{len(handles)}] Download error for '{s.name}': {s.error}")
                        handle._error_printed = True # Set the flag
                else:
                    active_downloads += 1 # Still active if not finished and no error

                    # Print progress for active torrents
                    # Get torrent info only if metadata is available
                    torrent_name = s.name if s.has_metadata else f"Fetching metadata ({s.progress*100:.2f}%)"

                    print(f"\r[{i+1}/{len(handles)}] {torrent_name[:40].ljust(40)} | "
                          f"Progress: {s.progress*100:.2f}% | "
                          f"DL: {s.download_rate / 1000:.2f} kB/s | "
                          f"UP: {s.upload_rate / 1000:.2f} kB/s | "
                          f"Peers: {s.num_peers} | "
                          f"State: {state_str[s.state]}     ", end='')

            if active_downloads > 0: # Only sleep and wait for alerts if there are still active downloads
                ses.wait_for_alert(1000) # Corrected from wait_for_alerts to wait_for_alert
                time.sleep(1) # Wait for 1 second before updating again
            else:
                # Break the loop if no more active downloads (all finished or errored)
                break

        print("\nAll torrents have finished or encountered an error. Shutting down session.")
        ses = None # This will close the session and release resources

    print("\n--- Script setup instructions ---")
    print("To run this script:")
    print("1. Save the code above as a Python file (e.g., `torrent_downloader.py`).")
    print("2. Open your command prompt (CMD) or PowerShell.")
    print("3. Navigate to the directory where you saved the file using `cd path\\to\\your\\directory`.")
    print("4. Install `libtorrent` by running: `pip install python-libtorrent`")
    print("5. Run the script: `python torrent_downloader.py`")
    print("\n--- Important Considerations ---")
    print("- **Legal & Security:** Be mindful of copyright laws and security risks when downloading content via torrents.")
    print("- **Firewall:** Ensure your firewall allows Python to make network connections for torrenting.")
    "- **DHT Routers:** Uncomment `ses.add_dht_router` lines for faster peer discovery, especially for magnet links."
    "- **Port Forwarding:** For better download speeds and seeding, you might consider setting up port forwarding on your router for the port you listen on (e.g., 6881)."
    print("\n--- End of Script ---")
    print("Thank you for using the Torrent Downloader script!")