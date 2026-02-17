"""YouTube upload via Data API v3 with OAuth 2.0."""
from pathlib import Path
from typing import Optional

from src.config import CONFIG_DIR


def log(msg: str) -> None:
    print(f"[upload] {msg}")


def upload_to_youtube(
    video_path: Path,
    title: str,
    description: str,
) -> Optional[str]:
    """Upload a video to YouTube as a Short.

    Returns the video ID on success, or None if auth is missing.
    """
    token_path = CONFIG_DIR / "youtube-oauth.json"
    if not token_path.exists():
        log("config/youtube-oauth.json not found. Run: python scripts/auth_youtube.py")
        return None

    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

    creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            client_secrets = CONFIG_DIR / "client_secrets.json"
            if not client_secrets.exists():
                log("config/client_secrets.json not found. "
                    "Get OAuth client ID (Desktop) from Google Cloud Console.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets), SCOPES)
            creds = flow.run_local_server(port=0)

        # Save refreshed/new token
        with open(token_path, "w") as f:
            f.write(creds.to_json())

    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "categoryId": "22",
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(str(video_path), mimetype="video/mp4", resumable=True)
    request = youtube.videos().insert(
        part="snippet,status", body=body, media_body=media
    )
    response = request.execute()
    video_id = response.get("id")
    log(f"Uploaded: https://youtube.com/shorts/{video_id}")
    return video_id
