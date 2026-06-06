import os
import re
import time
import subprocess
import threading
import requests as req
from flask import Flask, render_template, request, jsonify, send_from_directory
import config
import yt_dlp


app = Flask(__name__)

app.config['DOWNLOAD_FOLDER'] = config.DOWNLOAD_PATH
app.config['PORT'] = config.PORT
app.config['HOST'] = config.HOST
app.config['DEBUG'] = config.DEBUG
app.config['YT_DLP_OPTIONS'] = config.get_yt_dlp_options(config.DOWNLOAD_PATH)

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


@app.route('/downloads/<path:filename>')
def download_file(filename):
    """Serve downloaded file."""
    return send_from_directory(app.config['DOWNLOAD_FOLDER'], filename, as_attachment=True)


def _make_thread_prefix(board, thread_no, op_post):
    subject = op_post.get('sub', '') or ''
    # Strip HTML tags (subject can contain <wbr> etc.)
    subject = re.sub(r'<[^>]+>', '', subject).strip()
    if not subject:
        subject = thread_no
    # Sanitize: keep alphanumeric, spaces, hyphens; collapse and replace spaces
    subject = re.sub(r'[^\w\s-]', '', subject)
    subject = re.sub(r'\s+', '_', subject.strip())
    subject = subject[:60].rstrip('_')
    return f'{board}_{subject}'


def _convert_webm_to_mp4(webm_path):
    mp4_path = os.path.splitext(webm_path)[0] + '.mp4'
    subprocess.run(
        ['ffmpeg', '-i', webm_path, '-c:v', 'libx264', '-c:a', 'aac', '-y', mp4_path],
        check=True, capture_output=True
    )
    os.remove(webm_path)
    return mp4_path


def _classify_4chan_url(url):
    if re.search(r'boards\.4chan(?:nel)?\.org/[^/]+/thread/\d+', url):
        return 'thread'
    if re.search(r'i\.4cdn\.org/', url):
        return 'file'
    return 'unknown'


_BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
}


def download_4chan(url, download_id, convert_webm=False):
    """Download 4chan thread media or single file in background thread."""
    try:
        download_status[download_id] = {
            'status': 'downloading',
            'progress': 0,
            'filename': None,
            'error': None,
            'files_done': 0,
            'files_total': 0,
        }

        download_folder = app.config['DOWNLOAD_FOLDER']
        url_type = _classify_4chan_url(url)
        session = req.Session()
        session.headers.update(_BROWSER_HEADERS)

        if url_type == 'thread':
            m = re.search(r'boards\.4chan(?:nel)?\.org/([^/]+)/thread/(\d+)', url)
            board = m.group(1)
            thread_no = m.group(2)

            # Visit the thread page first so the session picks up any cookies
            session.get(f'https://boards.4chan.org/{board}/thread/{thread_no}', timeout=15)

            api_url = f'https://a.4cdn.org/{board}/thread/{thread_no}.json'
            r = session.get(api_url, timeout=30)
            r.raise_for_status()
            thread_data = r.json()

            posts = thread_data.get('posts', [])
            prefix = _make_thread_prefix(board, thread_no, posts[0] if posts else {})
            thread_dir = os.path.join(download_folder, prefix)
            os.makedirs(thread_dir, exist_ok=True)

            media_files = []
            for post in posts:
                if post.get('tim') and post.get('ext'):
                    name = post.get('filename') or str(post['tim'])
                    media_files.append({
                        'url': f'https://i.4cdn.org/{board}/{post["tim"]}{post["ext"]}',
                        'filename': f'{prefix}_{name}{post["ext"]}',
                    })
                for extra in post.get('extra_files', []):
                    if extra.get('tim') and extra.get('ext'):
                        name = extra.get('filename') or str(extra['tim'])
                        media_files.append({
                            'url': f'https://i.4cdn.org/{board}/{extra["tim"]}{extra["ext"]}',
                            'filename': f'{prefix}_{name}{extra["ext"]}',
                        })

            download_status[download_id]['files_total'] = len(media_files)

            last_filename = None
            for i, media in enumerate(media_files):
                file_path = os.path.join(thread_dir, media['filename'])
                if not os.path.exists(file_path):
                    r = session.get(media['url'], timeout=60, stream=True,
                                    headers={'Referer': f'https://boards.4chan.org/{board}/thread/{thread_no}',
                                             'Accept': '*/*',
                                             'Sec-Fetch-Dest': 'video',
                                             'Sec-Fetch-Mode': 'no-cors',
                                             'Sec-Fetch-Site': 'cross-site'})
                    r.raise_for_status()
                    with open(file_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                    if convert_webm and file_path.endswith('.webm'):
                        file_path = _convert_webm_to_mp4(file_path)
                        media['filename'] = os.path.basename(file_path)
                    time.sleep(0.5)
                last_filename = media['filename']
                download_status[download_id]['files_done'] = i + 1
                download_status[download_id]['progress'] = int(((i + 1) / len(media_files)) * 100)

            download_status[download_id]['status'] = 'completed'
            download_status[download_id]['progress'] = 100
            download_status[download_id]['filename'] = last_filename

        else:
            filename = url.split('/')[-1].split('?')[0]
            file_path = os.path.join(download_folder, filename)

            r = session.get(url, timeout=60, stream=True,
                            headers={'Accept': '*/*', 'Referer': 'https://boards.4chan.org/'})
            r.raise_for_status()

            total = int(r.headers.get('content-length', 0))
            downloaded = 0
            with open(file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        download_status[download_id]['progress'] = int((downloaded / total) * 100)

            download_status[download_id]['status'] = 'completed'
            download_status[download_id]['progress'] = 100
            download_status[download_id]['filename'] = filename

    except Exception as e:
        download_status[download_id]['status'] = 'error'
        download_status[download_id]['error'] = str(e)


@app.route('/4chan', methods=['POST'])
def start_4chan_download():
    """Start a 4chan thread or file download."""
    data = request.get_json()
    url = data.get('url', '').strip()

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    if _classify_4chan_url(url) == 'unknown':
        return jsonify({'error': 'URL must be a 4chan thread (boards.4chan.org/.../thread/...) or a direct file (i.4cdn.org/...)'}), 400

    convert_webm = bool(data.get('convert_webm', False))
    download_id = str(len(download_status) + 1)
    thread = threading.Thread(target=download_4chan, args=(url, download_id, convert_webm))
    thread.daemon = True
    thread.start()

    return jsonify({'download_id': download_id, 'status': 'started'})


@app.route('/files')
def list_files():
    """List all downloaded files, including those in subdirectories."""
    files = []
    download_folder = app.config['DOWNLOAD_FOLDER']

    if os.path.exists(download_folder):
        for dirpath, _, filenames in os.walk(download_folder):
            for filename in filenames:
                if filename == '.gitkeep':
                    continue
                filepath = os.path.join(dirpath, filename)
                rel_path = os.path.relpath(filepath, download_folder)
                files.append({
                    'name': rel_path,
                    'size': os.path.getsize(filepath),
                    'url': f'/downloads/{rel_path}'
                })

    return jsonify(files)


if __name__ == '__main__':
    app.run(
        debug=app.config['DEBUG'],
        host=app.config['HOST'],
        port=app.config['PORT']
    )
