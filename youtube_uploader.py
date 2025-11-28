import os
import sys
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Scopes needed for uploading
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def authenticate_youtube():
    """Handles OAuth2 authentication with YouTube."""
    creds = None
    # The file token.json stores the user's access and refresh tokens.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "client_secrets.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    
    return build("youtube", "v3", credentials=creds)

def upload_video(file_path, title, description, tags, category_id="22"):
    """Uploads a video to YouTube."""
    youtube = authenticate_youtube()
    
    print(f"🚀 Uploading {file_path}...")
    
    body = {
        "snippet": {
            "title": title[:100],  # Max 100 chars
            "description": description[:5000],
            "tags": tags,
            "categoryId": category_id
        },
        "status": {
            "privacyStatus": "private", # Start private to check for copyright
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(
        file_path, 
        chunksize=-1, 
        resumable=True, 
        mimetype="video/mp4"
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%")

    print(f"✅ Upload Complete! Video ID: {response.get('id')}")
    return response.get('id')

if __name__ == "__main__":
    # Example usage
    if len(sys.argv) > 1:
        vid_path = sys.argv[1]
        upload_video(vid_path, "Automated Short", "#shorts #ai", ["shorts", "automation"])
    else:
        print("Please provide a video path as an argument.")