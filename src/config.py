import os


DOWNLOAD_PATH = os.environ.get('DOWNLOADER_OUTPUT_DIR', 'downloads')
PORT = int(os.environ.get('DOWNLOADER_PORT', 5067))
HOST = os.environ.get('DOWNLOADER_HOST', '0.0.0.0')
DEBUG = os.environ.get('DOWNLOADER_DEBUG', '').lower() in ('1', 'true', 'yes')


def get_yt_dlp_options(download_folder):
    return {
        'format': 'best',
        'outtmpl': os.path.join(download_folder, '%(title)s.%(ext)s'),
        'quiet': False,
        'no_warnings': False,
    }
