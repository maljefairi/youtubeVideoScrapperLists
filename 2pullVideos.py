import os
import csv
import logging
import time
from queue import Queue
from threading import Thread
from dotenv import load_dotenv
import yt_dlp
import glob

# Load environment variables
load_dotenv()

# Configuration
OUTPUT_DIRECTORY = os.getenv('OUTPUT_DIRECTORY', './output')
DOWNLOAD_DIRECTORY = os.getenv('DOWNLOAD_DIRECTORY', './downloaded_videos')
CHANNEL_FILE = os.getenv('CHANNEL_FILE', 'youtubeChannels.txt')
OUTPUT_FILE = os.getenv('OUTPUT_FILE', 'output.csv')
MAX_RETRIES = 10
THREADS = 3
LOG_FILE = 'download_log.txt'

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

# Ensure output directory exists
os.makedirs(DOWNLOAD_DIRECTORY, exist_ok=True)

# Initialize queue
download_queue = Queue()

def download_video(video_url, output_path):
    ydl_opts = {
        'format': 'best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([video_url])
            return True
        except Exception as e:
            logging.error(f"Error downloading {video_url}: {str(e)}")
            return False

def worker():
    while True:
        video_info = download_queue.get()
        if video_info is None:
            break
        
        video_url, video_id, channel_name = video_info
        output_path = os.path.join(DOWNLOAD_DIRECTORY, channel_name, f'{video_id}.%(ext)s')
        
        # Ensure channel directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        for attempt in range(MAX_RETRIES):
            if download_video(video_url, output_path):
                logging.info(f"Successfully downloaded: {video_url}")
                break
            else:
                if attempt < MAX_RETRIES - 1:
                    logging.warning(f"Retry {attempt + 1} for {video_url}")
                    time.sleep(5)  # Wait 5 seconds before retrying
                else:
                    logging.error(f"Failed to download after {MAX_RETRIES} attempts: {video_url}")
        
        download_queue.task_done()

def read_channel_names(filename):
    try:
        with open(filename, 'r') as file:
            return file.read().splitlines()
    except FileNotFoundError:
        logging.error(f"Channel file not found: {filename}")
        return []

def main():
    channel_names = read_channel_names(CHANNEL_FILE)
    
    for channel_name in channel_names:
        csv_file = os.path.join(OUTPUT_DIRECTORY, f"{channel_name}_{OUTPUT_FILE}")
        
        if not os.path.exists(csv_file):
            logging.warning(f"CSV file not found for channel {channel_name}: {csv_file}")
            continue
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    video_url = row['url']
                    video_id = video_url.split('v=')[-1]
                    download_queue.put((video_url, video_id, channel_name))
        except Exception as e:
            logging.error(f"Error reading CSV file {csv_file}: {str(e)}")

    # Start worker threads
    threads = []
    for _ in range(THREADS):
        t = Thread(target=worker)
        t.start()
        threads.append(t)

    # Wait for all tasks to be completed
    download_queue.join()

    # Stop workers
    for _ in range(THREADS):
        download_queue.put(None)
    for t in threads:
        t.join()

    logging.info("All downloads completed.")

if __name__ == "__main__":
    main()