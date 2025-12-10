import os
import threading
from flask import Flask, render_template, request, jsonify, send_from_directory
from config import get_yt_dlp_options
from args import parse_args
import yt_dlp


# Parse command line arguments
args = parse_args()

app = Flask(__name__)

# Configure app from command line arguments
app.config['DOWNLOAD_FOLDER'] = args.download_folder
app.config['PORT'] = args.port
app.config['HOST'] = args.host
app.config['DEBUG'] = args.debug
app.config['YT_DLP_OPTIONS'] = get_yt_dlp_options(args.download_folder)

# Ensure download folder exists
os.makedirs(app.config['DOWNLOAD_FOLDER'], exist_ok=True)

# Store download status
download_status = {}


def download_video(url, download_id, format_type='video'):
    """Download video in background thread."""
    try:
        download_status[download_id] = {
            'status': 'downloading',
            'progress': 0,
            'filename': None,
            'error': None
        }

        def progress_hook(d):
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)
                if total > 0:
                    progress = int((downloaded / total) * 100)
                    download_status[download_id]['progress'] = progress
            elif d['status'] == 'finished':
                download_status[download_id]['status'] = 'completed'
                download_status[download_id]['progress'] = 100
                download_status[download_id]['filename'] = os.path.basename(d['filename'])

        ydl_opts = app.config['YT_DLP_OPTIONS'].copy()
        ydl_opts['progress_hooks'] = [progress_hook]

        # Set format based on user selection
        if format_type == 'audio':
            ydl_opts['format'] = 'bestaudio'
            # Extract audio and convert to mp3
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        else:
            ydl_opts['format'] = 'best'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

            # For audio, update filename extension to .mp3
            if format_type == 'audio':
                filename = os.path.splitext(filename)[0] + '.mp3'

            download_status[download_id]['filename'] = os.path.basename(filename)
            download_status[download_id]['status'] = 'completed'
            download_status[download_id]['progress'] = 100

    except Exception as e:
        download_status[download_id]['status'] = 'error'
        download_status[download_id]['error'] = str(e)


@app.route('/')
def index():
    """Render main page."""
    return render_template('index.html')


@app.route('/download', methods=['POST'])
def start_download():
    """Start video download."""
    data = request.get_json()
    url = data.get('url')
    format_type = data.get('format', 'video')  # Default to video if not specified

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    if format_type not in ['audio', 'video']:
        return jsonify({'error': 'Format must be either "audio" or "video"'}), 400

    # Generate unique download ID
    download_id = str(len(download_status) + 1)

    # Start download in background thread
    thread = threading.Thread(target=download_video, args=(url, download_id, format_type))
    thread.daemon = True
    thread.start()

    return jsonify({
        'download_id': download_id,
        'status': 'started'
    })


@app.route('/status/<download_id>')
def get_status(download_id):
    """Get download status."""
    if download_id not in download_status:
        return jsonify({'error': 'Download not found'}), 404

    return jsonify(download_status[download_id])


@app.route('/downloads/<filename>')
def download_file(filename):
    """Serve downloaded file."""
    return send_from_directory(app.config['DOWNLOAD_FOLDER'], filename, as_attachment=True)


@app.route('/files')
def list_files():
    """List all downloaded files."""
    files = []
    download_folder = app.config['DOWNLOAD_FOLDER']

    if os.path.exists(download_folder):
        for filename in os.listdir(download_folder):
            filepath = os.path.join(download_folder, filename)
            if os.path.isfile(filepath) and filename != '.gitkeep':
                files.append({
                    'name': filename,
                    'size': os.path.getsize(filepath),
                    'url': f'/downloads/{filename}'
                })

    return jsonify(files)


if __name__ == '__main__':
    app.run(
        debug=app.config['DEBUG'],
        host=app.config['HOST'],
        port=app.config['PORT']
    )
