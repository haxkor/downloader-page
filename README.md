# Video Downloader Web App

A Flask-based web application for downloading videos from YouTube and other platforms using yt-dlp.

## Features

- Simple web interface for entering video URLs
- Choose between video or audio-only downloads
- Audio files automatically converted to MP3 format
- Real-time download progress tracking
- View and download previously saved files
- Support for multiple video platforms via yt-dlp

## Setup

1. Install FFmpeg (required for audio conversion):
   ```bash
   # macOS
   brew install ffmpeg

   # Ubuntu/Debian
   sudo apt install ffmpeg

   # Windows: Download from https://ffmpeg.org/download.html
   ```

2. Clone the repository

3. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

6. Run the application:
   ```bash
   python app.py
   ```

7. Open http://localhost:5067 in your browser

## Usage

1. Enter a video URL in the input field
2. Select format: **Video** (full video with audio) or **Audio Only** (MP3)
3. Click "Download" button
4. Watch the real-time progress bar
5. Find your downloaded file in the "Downloaded Files" section

## Configuration

Edit `.env` file to customize:
- `DOWNLOAD_FOLDER`: Where videos are saved (default: downloads)
- `MAX_CONTENT_LENGTH`: Maximum file size in bytes (default: 500MB)
- `SECRET_KEY`: Flask secret key (change in production)

## Production Deployment

Use a production WSGI server like gunicorn:

```bash
gunicorn -w 4 -b 0.0.0.0:5067 app:app
```

**Note**: Ensure FFmpeg is installed on the production server for audio conversion to work.

## License

MIT
