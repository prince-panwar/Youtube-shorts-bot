# 🤖 AI YouTube Shorts Generator & Uploader

An automated bot that generates, edits, and uploads YouTube Shorts completely autonomously. It uses **Gemini AI** for scripting and metadata, **Pexels** for stock footage, **Edge TTS** for voiceovers, and **MoviePy** for video editing.

## ✨ Features

- **Trend Discovery**: Fetches trending topics from Google Trends RSS.
- **AI Scripting**: Generates engaging scripts and visual cues using Google Gemini.
- **Dynamic Editing**:
  - Downloads relevant stock footage from Pexels.
  - Generates high-quality voiceovers (Edge TTS).
  - Stitches clips with smooth fade transitions.
  - Adds "Shorts-style" big, bold subtitles.
- **Auto-Upload**: Uploads the final video to YouTube with AI-generated Title, Description, and Tags.
- **Scheduling**: Runs automatically every 4 hours to maximize growth while staying within API limits.

## 🛠️ Prerequisites

- **Python 3.10+**
- **FFmpeg** (Required for MoviePy)
- **API Keys**:
  - **Google Gemini API Key**: [Get it here](https://aistudio.google.com/)
  - **Pexels API Key**: [Get it here](https://www.pexels.com/api/)
- **YouTube Data API Credentials**:
  - Create a project in [Google Cloud Console](https://console.cloud.google.com/).
  - Enable "YouTube Data API v3".
  - Create "OAuth 2.0 Client IDs" (Desktop App).
  - Download the JSON file and rename it to `client_secrets.json`.

## 🚀 Setup

1.  **Clone the Repository**

    ```bash
    git clone <your-repo-url>
    cd youtubebot
    ```

2.  **Install Dependencies**

    ```bash
    pip install -r requirements.txt
    ```

    _(Note: If `requirements.txt` is missing, install manually: `pip install moviepy google-generativeai requests edge-tts google-auth-oauthlib google-api-python-client python-dotenv`)_

3.  **Configure Environment**
    Create a `.env` file in the root directory:

    ```ini
    PEXELS_API_KEY="your_pexels_key_here"
    GEMINI_API_KEY="your_gemini_key_here"
    ```

4.  **Setup YouTube Auth**
    - Place your `client_secrets.json` in the project root.
    - Run the uploader once manually to authenticate:
      ```bash
      python3 youtube_uploader.py output/final_short.mp4
      ```
    - Follow the link, authorize, and it will save a `token.json` for future auto-logins.

## 🏃 Usage

### Manual Run (Single Video)

To generate and upload one video immediately:

```bash
python3 shorts_generator.py
```

### Automated Scheduler (24/7)

To run the bot continuously (every 4 hours):

```bash
python3 scheduler.py
```

_Check `scheduler.log` to monitor progress._

## ⚠️ Quotas & Limits

- **YouTube Uploads**: The scheduler is set to 6 videos/day to stay safely under the 10,000 unit daily quota.
- **Pexels**: Free tier has generous limits but monitor usage if scaling up.
- **Gemini**: Free tier has rate limits; the script handles basic errors but paid tier is recommended for heavy use.

## 📂 Project Structure

- `shorts_generator.py`: Main logic (Trend -> Script -> Edit -> Upload).
- `youtube_uploader.py`: Handles YouTube API authentication and uploading.
- `scheduler.py`: Runs the generator at fixed intervals.
- `assets/`: Temporary storage for downloaded videos and audio (auto-cleaned).
- `output/`: Stores the final generated video.
