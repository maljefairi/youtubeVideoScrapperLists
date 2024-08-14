### README.md

```markdown
# YouTube Channel Video Scraper and Downloader

This project includes tools to scrape video information from YouTube channels and download videos. It consists of two main scripts:
1. A YouTube channel video scraper that fetches video information and generates transcripts.
2. A video downloader that processes the scraped information and downloads the videos.

## Setup

1. **Clone the Repository:**
   ```
   git clone <repository-url>
   ```

2. **Create and Activate a Virtual Environment:**
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
   ```

3. **Install Dependencies:**
   ```
   pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib google.generativeai python-dotenv yt-dlp
   ```

4. **Environment Setup:**
   Create a `.env` file based on the `.env.example` and fill in your credentials and configuration:

   ```
   YOUTUBE_API_KEY=your_youtube_api_key_here
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-1.5-flash
   CHANNEL_FILE=youtubeChannels.txt
   DATA_FILE=channel_data.csv
   OUTPUT_FILE=output.csv
   OUTPUT_DIRECTORY=./output
   DOWNLOAD_DIRECTORY=./downloaded_videos
   TRANSCRIPT_LANGUAGE=en-US
   MAX_VIDEOS_PER_CHANNEL=50
   LOG_LEVEL=INFO
   ```

5. **Prepare Input Files:**
   - `prompt.txt`: Contains the prompt template for generating transcripts.
   - `youtubeChannels.txt`: List of YouTube channel names.

## Usage

### 1. YouTube Channel Video Scraper

Execute the scraper script to collect video information:

```
python youtubeScrabber.py
```

### 2. Video Downloader

Run the downloader script to download the videos:

```
python integrated_youtube_downloader.py
```

## Important Notes

- Please adhere to YouTube's terms of service and copyright laws when using these scripts.
- Be aware of API quotas and rate limits to avoid potential blocks or penalties.
- The usage of the Gemini AI model requires appropriate permissions and credits.

## Troubleshooting

- Check your API keys and quotas for errors.
- Verify Gemini AI settings for issues.
- Adjust script settings if downloads fail, such as reducing the number of threads or increasing delay times.

## Customization

- Update `prompt.txt` to change transcript generation.
- Modify download settings in the downloader script for different video formats or qualities.

## License

This project is open-sourced under the MIT License. See the LICENSE file for more details.
```

### LICENSE

```markdown
MIT License

Copyright (c) 2023 <your name>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
