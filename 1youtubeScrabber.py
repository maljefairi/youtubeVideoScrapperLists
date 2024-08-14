import os
import csv
import logging
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import google.auth.exceptions
from dotenv import load_dotenv
import time
from datetime import datetime, timezone

# Load environment variables
load_dotenv()
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = os.getenv('GEMINI_MODEL')
CHANNEL_FILE = os.getenv('CHANNEL_FILE')
DATA_FILE = os.getenv('DATA_FILE')
OUTPUT_FILE = os.getenv('OUTPUT_FILE')
TRANSCRIPT_LANGUAGE = os.getenv('TRANSCRIPT_LANGUAGE', 'en-US')
MAX_VIDEOS_PER_CHANNEL = int(os.getenv('MAX_VIDEOS_PER_CHANNEL', 50))
OUTPUT_DIRECTORY = os.getenv('OUTPUT_DIRECTORY', './output')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Set up logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL), 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize YouTube API client
def youtube_client():
    try:
        return build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    except google.auth.exceptions.DefaultCredentialsError as e:
        logging.error(f"Authentication failure: {str(e)}")
        return None

# Initialize Gemini AI
try:
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)
except ImportError as e:
    logging.error(f"Failed to import Google Generative AI module: {str(e)}")
    model = None
except Exception as e:
    logging.error(f"Error initializing Gemini AI: {str(e)}")
    model = None

# Load prompt from file
def load_prompt():
    try:
        with open('prompt.txt', 'r') as file:
            return file.read()
    except FileNotFoundError:
        logging.error("prompt.txt file not found.")
        return ""

# Function to generate transcript and summary using Gemini AI
def generate_transcript_and_summary(video_url):
    if not model:
        return "TRANSCRIPT:\nError: Gemini AI not initialized\n\nSUMMARY:\nError: Gemini AI not initialized"
    
    prompt_template = load_prompt()
    if not prompt_template:
        return "TRANSCRIPT:\nError: Prompt template not found\n\nSUMMARY:\nError: Prompt template not found"
    
    prompt = prompt_template.format(video_url=video_url, language=TRANSCRIPT_LANGUAGE)
    try:
        response = model.generate_content(prompt)
        if response.text:
            return response.text
        else:
            logging.error(f"Empty response from Gemini AI for video: {video_url}")
            return "TRANSCRIPT:\nError: Empty response from AI\n\nSUMMARY:\nError: Empty response from AI"
    except Exception as e:
        logging.error(f"Error generating content for {video_url}: {str(e)}")
        return f"TRANSCRIPT:\nError generating transcript: {str(e)}\n\nSUMMARY:\nError generating summary: {str(e)}"

# Function to get channel ID by name
def get_channel_id(youtube, channel_name):
    try:
        response = youtube.search().list(q=channel_name, type='channel', part='id', maxResults=1).execute()
        if response['items']:
            return response['items'][0]['id']['channelId']
    except HttpError as e:
        logging.error(f"HTTP error when searching for channel {channel_name}: {e}")
    return None

# Get uploads playlist ID from channel ID
def get_uploads_playlist(youtube, channel_id):
    try:
        response = youtube.channels().list(id=channel_id, part='contentDetails').execute()
        return response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    except HttpError as e:
        logging.error(f"HTTP error when getting uploads playlist for channel {channel_id}: {e}")
    return None

# Fetch all videos from a playlist
def fetch_playlist_videos(youtube, playlist_id, last_checked):
    page_token = None
    while True:
        try:
            res = youtube.playlistItems().list(playlistId=playlist_id, part='snippet', maxResults=50, pageToken=page_token).execute()
            for item in res['items']:
                published_at = datetime.strptime(item['snippet']['publishedAt'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                if published_at > last_checked:
                    yield item
                else:
                    return
            page_token = res.get('nextPageToken')
            if not page_token:
                break
        except HttpError as e:
            logging.error(f"HTTP error fetching playlist items: {e}")
            break

# Function to check if a video needs transcript update
def needs_transcript_update(video, existing_data):
    video_id = video['snippet']['resourceId']['videoId']
    return video_id not in existing_data or not existing_data[video_id].get('transcript')

# Function to read existing CSV data
def read_existing_csv(filename):
    existing_data = {}
    if os.path.exists(filename):
        with open(filename, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                video_id = row['url'].split('v=')[-1]
                existing_data[video_id] = row
    return existing_data

def save_to_csv(video, filename, existing_data):
    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
    full_path = os.path.join(OUTPUT_DIRECTORY, filename)
    fields = ['title', 'url', 'publishedAt', 'transcript', 'summary']
    mode = 'a' if os.path.exists(full_path) else 'w'
    with open(full_path, mode=mode, newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        if mode == 'w':
            writer.writeheader()
        
        video_id = video['snippet']['resourceId']['videoId']
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        
        if needs_transcript_update(video, existing_data):
            logging.info(f"Generating transcript for video: {video['snippet']['title']}")
            transcript_and_summary = generate_transcript_and_summary(video_url)
            
            # Handle cases where the response doesn't contain 'SUMMARY:'
            if 'SUMMARY:' in transcript_and_summary:
                transcript, summary = transcript_and_summary.split('SUMMARY:', 1)
                transcript = transcript.replace('TRANSCRIPT:', '').strip()
                summary = summary.strip()
            else:
                logging.warning(f"No summary found for video: {video['snippet']['title']}")
                transcript = transcript_and_summary.replace('TRANSCRIPT:', '').strip()
                summary = "No summary available"
        else:
            logging.info(f"Using existing transcript for video: {video['snippet']['title']}")
            transcript = existing_data[video_id].get('transcript', '')
            summary = existing_data[video_id].get('summary', '')
        
        writer.writerow({
            'title': video['snippet']['title'],
            'url': video_url,
            'publishedAt': video['snippet']['publishedAt'],
            'transcript': transcript,
            'summary': summary
        })
        logging.info(f"Saved data for video: {video['snippet']['title']}")

# Read channel names from a file
def read_channel_names(filename):
    try:
        with open(filename, 'r') as file:
            return file.read().splitlines()
    except FileNotFoundError:
        logging.error(f"Channel file not found: {filename}")
        return []

# Read channel data including last checked timestamps
def read_channel_data(filename):
    if not os.path.exists(filename):
        return {}
    with open(filename, 'r') as file:
        return {line.split(',')[0].strip(): datetime.strptime(line.split(',')[1].strip(), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                for line in file if line.strip()}

# Write updated channel data including last checked timestamps
def write_channel_data(filename, channel_data):
    with open(filename, 'w') as file:
        for channel, timestamp in channel_data.items():
            file.write(f"{channel},{timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')}\n")

# Main function to run the script
def main():
    youtube = youtube_client()
    if not youtube:
        logging.error("Failed to initialize YouTube client. Exiting.")
        return

    channel_data = read_channel_data(DATA_FILE)

    for name in read_channel_names(CHANNEL_FILE):
        logging.info(f"\nProcessing channel: {name}")
        channel_id = get_channel_id(youtube, name)
        last_checked = channel_data.get(name, datetime(1970, 1, 1, tzinfo=timezone.utc))
        logging.info(f"Last checked: {last_checked}")
        
        if channel_id:
            playlist_id = get_uploads_playlist(youtube, channel_id)
            if not playlist_id:
                logging.error(f"Failed to get uploads playlist for channel: {name}")
                continue

            existing_data = read_existing_csv(os.path.join(OUTPUT_DIRECTORY, f'{name}_{OUTPUT_FILE}'))
            latest_video_time = last_checked
            video_count = 0
            
            for video in fetch_playlist_videos(youtube, playlist_id, last_checked):
                if video_count >= MAX_VIDEOS_PER_CHANNEL:
                    logging.info(f"Reached maximum number of videos ({MAX_VIDEOS_PER_CHANNEL}) for {name}")
                    break
                video_time = datetime.strptime(video['snippet']['publishedAt'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                latest_video_time = max(latest_video_time, video_time)
                save_to_csv(video, f'{name}_{OUTPUT_FILE}', existing_data)
                video_count += 1
                logging.info(f"Processed video {video_count}: {video['snippet']['title']}")
            
            if video_count > 0:
                channel_data[name] = latest_video_time
                logging.info(f"Processed {video_count} new videos for {name}.")
            else:
                logging.info(f"No new videos found for {name} since last check.")
        else:
            logging.error(f"Failed to fetch data for channel: {name}")

    write_channel_data(DATA_FILE, channel_data)
    logging.info("\nScript execution completed.")

if __name__ == '__main__':
    main()