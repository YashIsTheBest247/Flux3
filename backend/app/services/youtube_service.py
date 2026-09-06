"""
YouTube Publishing Service

Loads stored OAuth credentials (refreshing the access token via the saved
refresh_token when needed) and uploads finished videos with a resumable upload.
Privacy defaults to "private" via settings.YOUTUBE_PRIVACY_STATUS.
"""
import logging
from pathlib import Path
from typing import List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from app.core.config import settings

logger = logging.getLogger(__name__)

# Full youtube scope (covers videos.insert). Must match the stored token's scope.
SCOPES = ["https://www.googleapis.com/auth/youtube"]


class YouTubeServiceError(Exception):
    """Raised when YouTube publishing cannot proceed."""


def _load_credentials() -> Credentials:
    """
    Load credentials from the stored token file and refresh them if expired.
    Re-saves the token file when the access token is refreshed.
    """
    token_file: Path = settings.YOUTUBE_TOKEN_FILE

    if not token_file or not token_file.exists():
        raise YouTubeServiceError(
            f"YouTube token file not found at {token_file}. "
            "Run the OAuth flow to create secrets/youtube_token.json."
        )

    creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)

    if not creds.valid:
        if creds.expired and creds.refresh_token:
            logger.info("YouTube access token expired; refreshing via refresh_token...")
            creds.refresh(Request())
            # Persist the refreshed token so we don't refresh on every call.
            token_file.write_text(creds.to_json(), encoding="utf-8")
            logger.info("Refreshed YouTube token saved.")
        else:
            raise YouTubeServiceError(
                "Stored YouTube credentials are invalid and cannot be refreshed "
                "(missing refresh_token). Re-run the OAuth flow."
            )

    return creds


def _build_client():
    creds = _load_credentials()
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def upload_video(
    file_path: Path,
    title: str,
    description: str = "",
    tags: Optional[List[str]] = None,
    privacy_status: Optional[str] = None,
    category_id: Optional[str] = None,
) -> dict:
    """
    Upload a video file to YouTube and return {"video_id", "url"}.

    Raises YouTubeServiceError on any failure so the caller can log/handle it
    without crashing the whole pipeline.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise YouTubeServiceError(f"Video file not found: {file_path}")

    privacy = privacy_status or settings.YOUTUBE_PRIVACY_STATUS
    category = category_id or settings.YOUTUBE_CATEGORY_ID
    video_tags = tags if tags is not None else settings.youtube_tags_list

    # YouTube limits: title <= 100 chars, description <= 5000 chars.
    body = {
        "snippet": {
            "title": (title or "Untitled")[:100],
            "description": (description or "")[:5000],
            "tags": video_tags,
            "categoryId": category,
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    try:
        youtube = _build_client()
        media = MediaFileUpload(str(file_path), chunksize=-1, resumable=True)
        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        logger.info(f"Uploading '{file_path.name}' to YouTube (privacy={privacy})...")
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.info(f"YouTube upload progress: {int(status.progress() * 100)}%")

        video_id = response.get("id")
        url = f"https://youtu.be/{video_id}"
        logger.info(f"YouTube upload complete: {url}")
        return {"video_id": video_id, "url": url}

    except HttpError as exc:
        raise YouTubeServiceError(f"YouTube API error during upload: {exc}") from exc
    except YouTubeServiceError:
        raise
    except Exception as exc:  # noqa: BLE001 - surface any client/transport error
        raise YouTubeServiceError(f"Unexpected error during YouTube upload: {exc}") from exc
