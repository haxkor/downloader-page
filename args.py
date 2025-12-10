import argparse


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Video Downloader Web Application',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        '-p', '--port',
        type=int,
        default=5067,
        help='Port to run the application on'
    )

    parser.add_argument(
        '-d', '--download-folder',
        type=str,
        default='downloads',
        dest='download_folder',
        help='Folder to store downloaded files'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        default=False,
        help='Run in debug mode'
    )

    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='Host to bind the application to'
    )

    return parser.parse_args()
