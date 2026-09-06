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

# Must match what youtube_oauth requested. upload publishes the video;
# force-ssl is what allows thumbnails.set and captions.insert - an upload-only
# token fails on both with a bare 403.
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]


class YouTubeServiceError(Exception):
    """Raised when YouTube publishing cannot proceed."""


def _load_credentials() -> Credentials:
    """
    Load credentials, preferring the YOUTUBE_TOKEN_JSON env var (for deployments
    like Render where secrets/ is gitignored and the filesystem is ephemeral),
    falling back to the secrets/youtube_token.json file for local dev.
    Refreshes the access token when expired and persists it back when possible.
    """
    import json

    from app.services.credentials_service import PUBLISH_OWN, vault

    token_file: Path = settings.YOUTUBE_TOKEN_FILE

    # Which channel this upload belongs on. In "own" mode only the visitor's
    # connected token is acceptable - falling back to the deployment's own
    # channel would publish their video to someone else's account, which is the
    # worst possible failure mode here, so it fails loudly instead.
    if vault.publish_mode() == PUBLISH_OWN:
        token_json = (vault.get("YOUTUBE_TOKEN_JSON") or "").strip()
        if not token_json:
            raise YouTubeServiceError(
                "You chose to publish to your own channel but have not "
                "connected one yet. Connect it, or switch back to the default "
                "channel."
            )
    else:
        token_json = (settings.YOUTUBE_TOKEN_JSON or "").strip()

    if token_json:
        try:
            info = json.loads(token_json)
        except Exception as exc:  # noqa: BLE001
            raise YouTubeServiceError(
                f"YOUTUBE_TOKEN_JSON env var is not valid token JSON: {exc}"
            ) from exc
        try:
            # The token's OWN scopes, not the app's wish list. google-auth sends
            # whatever scopes it is holding on the refresh request, and Google
            # rejects a refresh that asks for scopes the grant never covered:
            # a token issued for `youtube` failed with `invalid_scope` the
            # moment this list was widened to upload+force-ssl. A refresh can
            # never change a grant, so it must never try to.
            creds = Credentials.from_authorized_user_info(info, info.get("scopes") or SCOPES)
        except Exception as exc:  # noqa: BLE001
            raise YouTubeServiceError(f"Stored YouTube token is unusable: {exc}") from exc
    elif token_file and token_file.exists():
        stored = json.loads(token_file.read_text(encoding="utf-8"))
        creds = Credentials.from_authorized_user_info(stored, stored.get("scopes") or SCOPES)
    else:
        raise YouTubeServiceError(
            f"No YouTube credentials found. Set YOUTUBE_TOKEN_JSON, or create "
            f"{token_file} via the OAuth flow (python authorize_youtube.py)."
        )

    if not creds.valid:
        if creds.expired and creds.refresh_token:
            logger.info("YouTube access token expired; refreshing via refresh_token...")
            creds.refresh(Request())
            # Best-effort persist of the refreshed token (no-op on read-only/ephemeral FS).
            try:
                if token_file:
                    token_file.parent.mkdir(parents=True, exist_ok=True)
                    token_file.write_text(creds.to_json(), encoding="utf-8")
                    logger.info("Refreshed YouTube token saved to file.")
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"Could not persist refreshed token (continuing): {exc}")
        else:
            raise YouTubeServiceError(
                "Stored YouTube credentials are invalid and cannot be refreshed "
                "(missing refresh_token). Re-run the OAuth flow."
            )

    return creds


def readiness() -> dict:
    """
    Can this deployment publish to YouTube? Reported by /health.

    Deliberately offline — it inspects the stored credentials rather than
    calling Google, so the health endpoint stays fast and quota-free. A
    configured-but-revoked token still reports ready; the upload itself is
    where that surfaces.
    """
    import json

    from app.services.credentials_service import PUBLISH_OWN, vault

    own_mode = vault.publish_mode() == PUBLISH_OWN
    vault_token = (vault.get("YOUTUBE_TOKEN_JSON") or "").strip()
    token_json = vault_token if own_mode else (settings.YOUTUBE_TOKEN_JSON or "").strip()
    token_file: Path = settings.YOUTUBE_TOKEN_FILE
    source = None
    detail = None

    if token_json:
        source = "your channel" if own_mode else "default channel"
        try:
            data = json.loads(token_json)
            if not data.get("refresh_token"):
                detail = "token has no refresh_token — it will stop working once it expires"
        except Exception as exc:  # noqa: BLE001
            return {"configured": True, "ready": False, "source": source,
                    "error": f"not valid token JSON: {exc}"}
    elif token_file and token_file.exists():
        source = str(token_file)
    else:
        return {
            "configured": False,
            "ready": False,
            "source": None,
            "mode": "own" if own_mode else "default",
            "error": (
                "You chose your own channel but have not connected one yet."
                if own_mode else
                "This deployment has no default channel configured. Set "
                "YOUTUBE_TOKEN_JSON, or connect your own channel instead."
            ),
        }

    # A grant for plain `youtube` can upload and set a thumbnail but NOT insert
    # a caption track - that needs force-ssl. Report it rather than letting the
    # creator discover it as a silent missing-captions warning per upload.
    granted = set()
    try:
        granted = set(json.loads(token_json).get("scopes") or [])
    except Exception:  # noqa: BLE001
        pass
    can_caption = bool(granted & {
        "https://www.googleapis.com/auth/youtube.force-ssl",
        "https://www.googleapis.com/auth/youtubepartner",
    })
    if not can_caption and granted:
        detail = (detail + " " if detail else "") + (
            "This token predates caption support: uploads and thumbnails work, "
            "but caption tracks need the youtube.force-ssl scope. Re-run "
            "authorize_youtube.py to add it."
        )

    return {
        "configured": True,
        "ready": True,
        "source": source,
        "can_caption": can_caption,
        "mode": "own" if own_mode else "default",
        "channel_title": vault.get("YOUTUBE_CHANNEL_TITLE", "") if own_mode
                         else settings.YOUTUBE_DEFAULT_CHANNEL_TITLE,
        "channel_url": _channel_url(own_mode),
        "channel_id": vault.get("YOUTUBE_CHANNEL_ID", "") if own_mode else "",
        "auto_upload": settings.YOUTUBE_AUTO_UPLOAD,
        "privacy_status": settings.YOUTUBE_PRIVACY_STATUS,
        "warning": detail,
    }


def _channel_url(own_mode: bool) -> str:
    """A public link to whichever channel this deployment publishes to.

    Prefers the id form for a connected channel because a handle is released
    the moment its owner changes it, and can then be claimed by anyone.
    """
    from app.services.credentials_service import vault

    if own_mode:
        channel_id = vault.get("YOUTUBE_CHANNEL_ID", "")
        if channel_id:
            return f"https://www.youtube.com/channel/{channel_id}"
    return (settings.YOUTUBE_CHANNEL_URL or "").strip()


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


def set_thumbnail(video_id: str, image_path: Path) -> bool:
    """Attach a custom thumbnail to an uploaded video.

    Returns False rather than raising on the one failure that is not a bug:
    custom thumbnails require a verified YouTube account, and an unverified
    channel gets a 403 here on every upload. Losing the whole publish over a
    thumbnail would be the wrong trade, so the caller logs it and moves on.
    """
    image_path = Path(image_path)
    if not image_path.exists():
        logger.warning("Thumbnail not found, skipping: %s", image_path)
        return False
    try:
        youtube = _build_client()
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(str(image_path), mimetype="image/jpeg"),
        ).execute()
        logger.info("Thumbnail set on %s", video_id)
        return True
    except HttpError as exc:
        if exc.resp.status == 403:
            logger.warning(
                "Thumbnail rejected for %s - custom thumbnails need a verified "
                "YouTube account (youtube.com/verify). The video is published "
                "and is using an auto-generated frame.", video_id,
            )
        else:
            logger.warning("Could not set thumbnail on %s: %s", video_id, exc)
        return False
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not set thumbnail on %s: %s", video_id, exc)
        return False


def upload_caption(video_id: str, srt_path: Path, language: str = "en",
                   name: str = "Captions") -> bool:
    """Attach an SRT caption track to an uploaded video.

    This is why the ingest pipeline never re-encodes an uploaded file. Burning
    subtitles into the pixels costs a full transcode - minutes of CPU and a
    memory peak a 512 MB instance cannot survive - whereas YouTube will happily
    take the .srt as a sidecar and render it itself, for free, in whatever
    player the viewer is using.
    """
    srt_path = Path(srt_path)
    if not srt_path.exists():
        logger.warning("Caption file not found, skipping: %s", srt_path)
        return False
    try:
        youtube = _build_client()
        youtube.captions().insert(
            part="snippet",
            body={"snippet": {"videoId": video_id, "language": language, "name": name}},
            media_body=MediaFileUpload(str(srt_path), mimetype="application/octet-stream"),
        ).execute()
        logger.info("Caption track uploaded for %s", video_id)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not upload captions for %s: %s", video_id, exc)
        return False


def channel_summary() -> Optional[dict]:
    """Channel title, subscriber and view counts for the dashboard header."""
    try:
        youtube = _build_client()
        response = youtube.channels().list(part="snippet,statistics", mine=True).execute()
        items = response.get("items") or []
        if not items:
            return None
        item = items[0]
        stats = item.get("statistics", {})
        snippet = item.get("snippet", {})
        return {
            "id": item.get("id"),
            "title": snippet.get("title"),
            "thumbnail": (snippet.get("thumbnails", {}).get("default") or {}).get("url"),
            "subscribers": stats.get("subscriberCount"),
            "views": stats.get("viewCount"),
            "videos": stats.get("videoCount"),
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not read channel summary: %s", exc)
        return None
