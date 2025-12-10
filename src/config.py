import os


def get_yt_dlp_options(download_folder):
    """Get yt-dlp options with the specified download folder.

    Args:
        download_folder: Path to the folder where downloads will be stored

    Returns:
        dict: yt-dlp configuration options
    """
    return {
        'format': 'best',
        'outtmpl': os.path.join(download_folder, '%(title)s.%(ext)s'),
        'quiet': False,
        'no_warnings': False,
    }
