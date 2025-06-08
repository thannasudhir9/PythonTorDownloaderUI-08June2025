# Python Torrent Downloader - Project Documentation

**Last Updated:** June 6, 2025

## Project Overview

This project is a web-based torrent downloader application built with Python, utilizing Flask for the web framework and `python-libtorrent` for the torrenting engine. It features a dynamic web interface for managing torrent downloads, with real-time status updates, and various user-friendly enhancements.

## Project Structure

```
PythonTorrentDownloader/
├── templates/
│   └── index.html       # Main HTML file for the web UI
├── torrentDownloaderUI.py # Flask application, backend logic, API endpoints
├── torrentDownloaderCLI.py # Command-line interface (separate functionality)
├── README.md              # This documentation file
└── requirements.txt       # Python package dependencies
```

## Architecture and Design

### Backend (`torrentDownloaderUI.py`)

*   **Framework:** Flask (a Python micro web framework).
*   **Torrent Engine:** `python-libtorrent` handles all torrent-related operations (adding, pausing, status, etc.).
*   **Threading:** A background thread (`update_torrent_status`) continuously polls `libtorrent` for status updates of active downloads and stores them for quick retrieval by the frontend.
*   **API Endpoints:** Flask routes are defined to handle frontend requests:
    *   `/`: Serves the main `index.html` page.
    *   `/add_torrent` (POST): Adds a new torrent via magnet link.
    *   `/get_status` (GET): Provides JSON data of current torrents and their statuses.
    *   `/control_torrent/<handle_id>/<action>` (POST): Pauses, resumes, or deletes a torrent.
    *   `/torrent_details/<handle_id>` (GET): Provides detailed file and peer info for a torrent.
    *   `/update_settings` (POST): Updates download/upload speed limits and max parallel downloads.
    *   `/control_selected` (POST): Performs bulk actions (pause, resume, delete) on selected torrents.
    *   `/set_file_priority/...` (POST): Sets priority for specific files within a torrent.
    *   `/get_ip_details` (GET): Fetches the server's public IP and approximate geolocation using `ip-api.com`.
*   **Key Python Modules Used:**
    *   `flask`: For the web server and routing.
    *   `libtorrent`: Core torrent session management and operations.
    *   `requests`: To make HTTP requests to the external IP geolocation API.
    *   `socket`: To determine the local IP address of the server.
    *   `threading`: To run the torrent status updates in a non-blocking background process.
    *   `os`: For path manipulations (e.g., determining download save path).
    *   `json`: For handling JSON data in API responses.

### Frontend (`templates/index.html`)

*   **Templating:** Flask renders `index.html`, passing initial data like the server IP.
*   **Styling:** Bootstrap 5.1.3 for responsive design and UI components. Custom CSS is included for theming (black, white, blue palette) and specific layout adjustments.
*   **JavaScript (Vanilla JS):**
    *   **Dynamic Updates:** Periodically fetches torrent statuses from `/get_status` (every 1 second) and updates the UI dynamically without full page reloads.
    *   **User Interactions:** Handles form submissions (adding torrents, settings), button clicks (pause, resume, delete, theme toggle, IP refresh), and modal dialogs for torrent details.
    *   **Theme Management:** Implements a light/dark theme toggle (with sun/moon icons) using Bootstrap's `data-bs-theme` attribute and `localStorage` to persist user preference.
    *   **Clipboard Integration:** Attempts to auto-paste magnet links from the clipboard when the 'Add New Torrent' input field is focused.
    *   **IP Display:** Fetches and displays the server's IP and location from `/get_ip_details`, with a refresh button.

## Functionality and Features

### Core Torrent Management

*   **Add Torrents:** Supports adding torrents via magnet links. The input field also attempts to auto-paste valid magnet links from the clipboard on focus.
*   **Download Path:** Torrents are saved to `~/Downloads/PythonTorrentDownloader/` by default. This path is created if it doesn't exist.
*   **Status Tracking:** Real-time updates for:
    *   Download/Upload Speed
    *   Progress (percentage)
    *   Number of Peers
    *   Current State (e.g., Downloading, Seeding, Paused, Finished)
*   **Torrent Controls:**
    *   Pause/Resume individual torrents.
    *   Delete individual torrents (removes from session, does not delete files by default through this UI action).
    *   Bulk control: Pause, Resume, Delete selected torrents.
*   **Detailed View:** A modal shows detailed information about a torrent, including:
    *   Individual files, their sizes, progress, and priority settings (Skip, Normal, High).
    *   Connected peers, their IP, client, speeds, and progress.
*   **Resume/Recheck Existing Files:** `libtorrent` automatically checks the specified `save_path` when a torrent is added. If files corresponding to the torrent already exist, it will verify them and resume downloading the remaining pieces or start seeding if complete. This process is inherent to `libtorrent`'s handling of adding torrents to a session with a valid save path.

### User Interface Enhancements

*   **Responsive Design:** Adapts to different screen sizes using Bootstrap.
*   **Theming:** 
    *   Custom black, white, and blue color scheme.
    *   Switchable Light/Dark mode with a sun/moon icon toggle in the top banner. Theme preference is saved in browser `localStorage`.
*   **VPN Warning:** A prominent banner at the top warns users to download only when connected to a VPN.
*   **Server IP and Location:** Displays the server's IP address and its approximate geographic location (e.g., City, Country) in the top banner. This information can be refreshed.
*   **Settings Panel:** Allows users to configure:
    *   Download Speed Limit (KB/s)
    *   Upload Speed Limit (KB/s)
    *   Maximum Parallel Downloads

### Setup and Run Instructions

1.  **Clone the Repository (Example):**
    ```bash
    git clone <repository_url>
    cd PythonTorrentDownloader
    ```

2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install Dependencies:**
    Make sure you have Python 3.x installed. Then, install the required packages:
    ```bash
    pip install -r requirements.txt
    ```
    *Note on `python-libtorrent`*: Installation can sometimes be tricky depending on your OS and Python version. If `pip install python-libtorrent` fails, you might need to find a pre-compiled wheel (`.whl`) file for your specific system or install it via a system package manager (e.g., `apt-get install python3-libtorrent` on Debian/Ubuntu, though version compatibility with the project might vary).

4.  **Run the Application:**
    ```bash
    python torrentDownloaderUI.py
    ```
    The application will start, and you should see output similar to:
    `Serving on http://<your_local_ip>:5000`

5.  **Access in Browser:**
    Open your web browser and navigate to `http://<your_local_ip>:5000` (e.g., `http://192.168.1.10:5000` or `http://127.0.0.1:5000` if running on the same machine).

## Development Log & Solutions (Recent Changes - June 6, 2025)

This section outlines recent significant features and changes implemented based on development interactions.

*   **UI Overhaul & Theming (June 6, 2025):**
    *   **Prompt:** Implement a new UI theme (black, white, blue accents) and a dark/light mode toggle.
    *   **Solution:** Modified `index.html` to include new CSS variables for theme colors, updated existing styles to use these variables. Added Bootstrap Icons for the theme toggle (sun/moon). JavaScript was added to manage theme state in `localStorage` and update the icon.

*   **Auto Clipboard Paste for Magnet Links (June 6, 2025):**
    *   **Prompt:** Add functionality to automatically paste a magnet link from the clipboard into the 'Add New Torrent' input field when it's focused.
    *   **Solution:** Added JavaScript in `index.html` to use the `navigator.clipboard.readText()` API on focus of the magnet link input field. It checks if the clipboard content is a valid magnet link and populates the field.

*   **VPN Warning Banner (June 6, 2025):**
    *   **Prompt:** Display a warning message about using a VPN.
    *   **Solution:** Added a fixed banner at the top of `index.html` with the warning text.

*   **Enhanced IP Display (June 6, 2025):**
    *   **Prompt:** Refresh the displayed server IP and show its location details.
    *   **Solution:** 
        *   Backend: Added a new Flask route `/get_ip_details` in `torrentDownloaderUI.py` that fetches the server's IP and uses `ip-api.com` (via `requests` library) to get geolocation data.
        *   Frontend: Updated `index.html` JavaScript to call this endpoint, display the IP and location, and added a refresh button.

*   **Dependency Management (June 6, 2025):**
    *   **Prompt:** Ensure all dependencies are tracked.
    *   **Solution:** Created `requirements.txt` listing `Flask`, `requests`, `python-libtorrent`, `humanize`, and `werkzeug`.

*   **Auto-Resume/Recheck Confirmation (June 6, 2025):**
    *   **Prompt:** Ensure the application auto-fetches progress and resumes downloads if files already exist.
    *   **Solution:** Confirmed that `libtorrent`'s default behavior when adding a torrent with a correct `save_path` (where files might exist) is to re-check and resume. No specific code changes were deemed necessary for this core `libtorrent` feature, as the existing implementation allows for it.

This README provides a comprehensive guide to the Python Torrent Downloader project. For further development or troubleshooting, refer to the respective Flask and libtorrent documentation.


# Install dependencies
pip install -r requirements.txt

# Run the application
python torrentDownloaderUI.py



add a postgres sql database, create user and store the information of magnet links , metadata , downloaded files etc specific to the user

create an admin user who can monitor number of users and what users have downloaded


taskkill /F /IM python.exe