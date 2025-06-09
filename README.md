# Torrent Downloader Web UI

**Last Updated:** June 9, 2025  
**Version:** 2.1.0

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.0+-blue.svg)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.1+-blueviolet.svg)

A modern, responsive web-based torrent downloader with a clean user interface, built with Python, Flask, and libtorrent. Features include real-time download monitoring, speed control, and support for both magnet links and .torrent files.

## 📚 Project Documentation

- [Product Requirements Document (PRD)](PRD.md) - Project scope and requirements
- [User Stories & Tasks](USER_STORIES_AND_TASKS.md) - Development tracking
- [Bug Tracker](BUGS.md) - Known issues and resolutions
- [Developer Guide](PROMPTS_AND_SOLUTIONS.md) - Common solutions and patterns

## ✨ Features

- 🎨 **Modern UI** with light/dark theme support
- 📱 **Fully responsive** design that works on all devices
- ⚡ **Real-time** download/upload speed monitoring
- 📊 **Interactive charts** for speed visualization
- 🔄 **Background processing** for uninterrupted downloads
- 🔒 **CSRF protection** for secure form submissions
- 🌐 **IP information** with geolocation
- ⚙️ **Customizable settings** for download/upload limits
- 📂 **File selection** for selective downloading
- 🔍 **Search and sort** functionality for downloads
- 📱 **Mobile-friendly** interface with touch support

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- libtorrent-rasterbar (Python bindings)

### Setup Instructions

1. **Install System Dependencies**
   ```bash
   # For Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install -y python3-pip python3-dev libboost-python-dev libssl-dev
   
   # Install libtorrent
   sudo apt-get install -y python3-libtorrent
   
   # For Windows, use pre-built binaries:
   # pip install python-libtorrent
   ```

2. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configuration**
   Copy `.env.example` to `.env` and modify the settings as needed:
   ```bash
   cp .env.example .env
   ```

4. **Run the Application**
   ```bash
   python torrentDownloaderUI.py
   ```
   The web interface will be available at `http://localhost:5000`

## 🏗️ Project Structure

```
PythonTorrentDownloader/
├── templates/              # HTML templates
│   ├── base.html          # Base template with common layout
│   └── index.html         # Main application interface
├── static/                # Static files
│   ├── css/               # Custom styles
│   ├── js/                # JavaScript files
│   └── img/               # Images and icons
├── torrentDownloaderUI.py  # Main Flask application
├── torrentDownloaderCLI.py # Command-line interface
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
└── README.md            # Documentation
```

## 🛠️ Configuration

Edit the `.env` file to customize the application settings:

```ini
# Application Settings
FLASK_ENV=development
SECRET_KEY=your-secret-key

# Torrent Settings
SAVE_PATH=./downloads
MAX_DOWNLOAD_SPEED=0        # 0 = unlimited (KB/s)
MAX_UPLOAD_SPEED=100       # 100 KB/s
MAX_ACTIVE_DOWNLOADS=5
MAX_ACTIVE_SEEDS=5

# Web UI Settings
DARK_MODE=false
REFRESH_INTERVAL=2000      # ms
THEME_COLOR=#4361ee
```

## 🖥️ Usage

### Adding Torrents
1. **Using Magnet Links**
   - Click the "Add Torrent" button
   - Paste the magnet link in the input field
   - Click "Download" to start

2. **Using .torrent Files**
   - Click "Choose File" in the Add Torrent section
   - Select your .torrent file
   - Click "Upload" to start downloading

### Managing Downloads
- **Pause/Resume**: Click the pause/resume button next to each torrent
- **Remove**: Click the delete button to remove a torrent (with data)
- **Priority**: Set file priority before starting the download
- **Speed Limits**: Adjust download/upload speeds in Settings

### Viewing Stats
- Real-time download/upload speeds
- Progress bars for each torrent
- Detailed file information
- Peer and seed information

## 🌐 API Documentation

### Authentication
All API endpoints require a valid session token. Include it in the headers:
```
X-CSRFToken: your-csrf-token
```

### Endpoints

#### List All Torrents
```
GET /api/torrents
```
**Response**
```json
{
  "torrents": [
    {
      "id": "abc123",
      "name": "Ubuntu 22.04",
      "progress": 75.5,
      "status": "downloading",
      "download_rate": 2.5,
      "upload_rate": 0.5,
      "size": 4500,
      "downloaded": 3400,
      "peers": 12,
      "seeds": 45
    }
  ]
}
```

#### Add New Torrent
```
POST /api/torrents
```
**Body**
```json
{
  "magnet": "magnet:?xt=urn:btih:...",
  "save_path": "/downloads",
  "paused": false
}
```

#### Get Torrent Details
```
GET /api/torrents/{torrent_id}
```

#### Pause/Resume Torrent
```
POST /api/torrents/{torrent_id}/pause
POST /api/torrents/{torrent_id}/resume
```

#### Delete Torrent
```
DELETE /api/torrents/{torrent_id}
```

## 🚀 Deployment

### Production Deployment with Gunicorn

1. **Install Gunicorn**
   ```bash
   pip install gunicorn
   ```

2. **Run with Gunicorn**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8000 torrentDownloaderUI:app
   ```
   This will start the server on port 8000 with 4 worker processes.

### Docker Deployment

1. **Build the Docker image**
   ```bash
   docker build -t torrent-downloader .
   ```

2. **Run the container**
   ```bash
   docker run -d -p 8000:8000 \
     -v $(pwd)/downloads:/app/downloads \
     -v $(pwd)/.env:/app/.env \
     --name torrent-downloader \
     torrent-downloader
   ```

### Systemd Service (Linux)

Create a systemd service file at `/etc/systemd/system/torrent-downloader.service`:

```ini
[Unit]
Description=Torrent Downloader Web UI
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/torrent-downloader
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn -w 4 -b 0.0.0.0:8000 torrentDownloaderUI:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Then enable and start the service:
```bash
sudo systemctl enable torrent-downloader
sudo systemctl start torrent-downloader
```

## 🔧 Troubleshooting

### Common Issues

1. **Libtorrent not found**
   ```
   ImportError: No module named libtorrent
   ```
   **Solution**: Install libtorrent for your platform:
   - Ubuntu: `sudo apt-get install python3-libtorrent`
   - Windows: `pip install python-libtorrent`
   - macOS: `brew install libtorrent-rasterbar`

2. **Permission Denied**
   ```
   PermissionError: [Errno 13] Permission denied: '/downloads'
   ```
   **Solution**: Ensure the download directory exists and is writable:
   ```bash
   sudo mkdir -p /downloads
   sudo chown -R $USER:$USER /downloads
   ```

3. **Port Already in Use**
   ```
   OSError: [Errno 98] Address already in use
   ```
   **Solution**: Either stop the process using the port or change the port in the configuration.

4. **Slow Download Speeds**
   - Check your internet connection
   - Increase the number of connections in settings
   - Try different trackers
   - Ensure your firewall isn't blocking connections

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Flask](https://flask.palletsprojects.com/)
- Torrent handling with [libtorrent](https://www.libtorrent.org/)
- Frontend powered by [Bootstrap 5](https://getbootstrap.com/)
- Icons from [Bootstrap Icons](https://icons.getbootstrap.com/)

## 🏗️ Architecture and Design

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


# TODO - prompts
add speed test in top and show download speed and upload speed of the current internet connection

add a postgres sql database, create user and store the information of magnet links , metadata , downloaded files etc specific to the user

create an admin user who can monitor number of users ,add users and see what users have downloaded

Show Completed Downloads in Green / Light Green Color
Hide Connected Peers and Files Section, only when clicked on current active torrent should be displayed

# Commands
taskkill /F /IM python.exe

python torrentDownloaderUI.py


# VPN - Using UrbanVPN windows application , connected to italy

# Educational Purposes Only

Date - June 8 2025