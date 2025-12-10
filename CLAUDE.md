# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Flask-based web application for downloading videos from YouTube and other platforms using yt-dlp. Users enter a URL through a web interface, select either video or audio-only format, and the server downloads the content to local storage. Audio downloads are automatically converted to MP3 format.

## Architecture

### Backend (Flask)
- **app.py**: Main Flask application with the following key components:
  - Background threading for async downloads to prevent blocking
  - In-memory status tracking using `download_status` dictionary
  - yt-dlp integration with progress hooks for real-time updates
  - RESTful API endpoints for download management

- **config.py**: Centralized configuration using environment variables
  - Loads from .env file via python-dotenv
  - Contains yt-dlp options and download settings

### Frontend
- **templates/index.html**: Single-page interface with download form, format selector, and file list
- **static/js/app.js**: Vanilla JavaScript handling:
  - Format selection (video or audio-only) via radio buttons
  - AJAX requests to backend API with format parameter
  - Polling mechanism (1-second intervals) for download status
  - Dynamic file list rendering
- **static/css/style.css**: Modern gradient UI with responsive design and styled radio buttons

### Data Flow
1. User submits URL and selects format (video/audio) via frontend form
2. POST to `/download` creates download task with unique ID and format parameter
3. Background thread executes yt-dlp download with appropriate format settings
4. For audio: yt-dlp downloads best audio and uses FFmpeg to convert to MP3
5. Frontend polls `/status/<id>` for progress updates
6. Completed files stored in `downloads/` folder
7. Files listed via `/files` endpoint and served via `/downloads/<filename>`

## Development Commands

### Initial Setup
```bash
# Install FFmpeg (required for audio conversion)
# macOS:
brew install ffmpeg
# Ubuntu/Debian:
sudo apt install ffmpeg
# Windows: Download from https://ffmpeg.org/download.html

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
```

### Running the Application
```bash
# Development mode (with auto-reload)
python app.py

# Production mode (using gunicorn)
gunicorn -w 4 -b 0.0.0.0:5067 app:app
```

The application runs on http://localhost:5067

### Dependency Management
```bash
# Add new dependency
pip install <package>
pip freeze > requirements.txt

# Update all dependencies
pip install --upgrade -r requirements.txt
```

## Key Technical Details

### Threading Model
Downloads run in daemon threads to prevent blocking the main Flask process. The `download_status` dictionary provides thread-safe status tracking. Note: This in-memory approach is suitable for single-server deployments only. For multi-server setups, use Redis or a database.

### yt-dlp Configuration and Format Selection
The application supports two download formats:
- **Video**: Uses `format: 'best'` to download the best quality video with audio
- **Audio Only**: Uses `format: 'bestaudio'` and includes FFmpeg postprocessor to extract audio and convert to MP3 (192kbps)

The `YT_DLP_OPTIONS` in config.py provides base configuration:
- `format`: Video quality selection (dynamically set based on user selection)
- `outtmpl`: Filename template for saved files
- `progress_hooks`: Custom callback for progress updates
- `postprocessors`: Added dynamically for audio downloads to convert to MP3

Format selection is handled in `download_video()` function (app.py:18-69):
- Receives format_type parameter ('video' or 'audio')
- Modifies yt-dlp options accordingly
- For audio, adds FFmpegExtractAudio postprocessor and updates file extension to .mp3

**Important**: FFmpeg must be installed on the system for audio conversion to work.

### File Storage
Downloaded files are stored in the `downloads/` folder with filenames based on video titles. The folder is git-ignored except for `.gitkeep`. Ensure sufficient disk space and consider implementing file cleanup for production use.

### API Endpoints
- `GET /`: Main web interface
- `POST /download`: Start download (expects JSON: `{"url": "...", "format": "video|audio"}`)
  - Returns: `{"download_id": "...", "status": "started"}`
  - Validates format parameter (must be 'video' or 'audio')
- `GET /status/<download_id>`: Get download progress
  - Returns: `{"status": "downloading|completed|error", "progress": 0-100, "filename": "...", "error": "..."}`
- `GET /files`: List all downloaded files with metadata
- `GET /downloads/<filename>`: Serve file for download

### Frontend Polling
The JavaScript client polls the status endpoint every 1 second while a download is active. The interval is cleared when download completes or fails to prevent unnecessary requests.

## Common Modifications

### Changing Download Location
Update `DOWNLOAD_FOLDER` in .env or modify `Config.DOWNLOAD_FOLDER` in config.py.

### Changing Audio Quality/Format
To modify audio conversion settings, edit the postprocessor in `download_video()` (app.py:47-51):
```python
'postprocessors': [{
    'key': 'FFmpegExtractAudio',
    'preferredcodec': 'mp3',  # Can be: mp3, aac, flac, wav, etc.
    'preferredquality': '192',  # Bitrate in kbps
}]
```

### Adding Video Quality Selection
1. Add quality dropdown/options in index.html (e.g., 720p, 1080p, 4K)
2. Update JavaScript to send quality parameter
3. Modify `download_video()` to accept quality parameter
4. Set `ydl_opts['format']` based on quality (e.g., 'bestvideo[height<=720]+bestaudio')

### Implementing Download History
Replace in-memory `download_status` with SQLite database:
1. Create models for downloads and files
2. Store metadata (URL, timestamp, status, filename)
3. Update status endpoints to query database

### Adding Authentication
Use Flask-Login or Flask-HTTPAuth:
1. Add user model and authentication routes
2. Protect download endpoints with `@login_required`
3. Update frontend to handle login/logout

## Security Considerations

- Validate and sanitize user-provided URLs to prevent malicious input
- Implement rate limiting to prevent abuse (use Flask-Limiter)
- Set appropriate file permissions on downloads folder
- Consider implementing file size limits via MAX_CONTENT_LENGTH
- Do not expose the downloads folder directly via web server in production
