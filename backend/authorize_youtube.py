"""
One-time YouTube OAuth authorization.

Regenerates secrets/youtube_token.json (with a fresh refresh_token) from your
existing secrets/youtube_client_secret.json. Run this whenever uploads fail with
'invalid_grant' (an expired/revoked refresh token).

Usage:
    # from the backend/ directory, with the venv active
    python authorize_youtube.py

It will open a browser for you to grant access, then save the token. After it
finishes, the auto-publish feature will work again.

Tip: if the OAuth consent screen is in "Testing" mode, Google expires refresh
tokens after 7 days. Set the consent screen to "In production" to avoid having
to re-run this every week.
"""
import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Full youtube scope (covers videos.insert). Must match what the app expects.
SCOPES = ["https://www.googleapis.com/auth/youtube"]

BASE_DIR = Path(__file__).resolve().parent
CLIENT_SECRET_FILE = BASE_DIR / "secrets" / "youtube_client_secret.json"
TOKEN_FILE = BASE_DIR / "secrets" / "youtube_token.json"


def main() -> int:
    if not CLIENT_SECRET_FILE.exists():
        print(f"ERROR: client secret not found at {CLIENT_SECRET_FILE}")
        print("Download an OAuth 'Desktop app' client from Google Cloud Console "
              "and save it there.")
        return 1

    creds = None

    # Reuse a still-valid token if one exists.
    if TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        except Exception:
            creds = None

    if creds and creds.valid:
        print("Existing token is already valid. Nothing to do.")
        return 0

    if creds and creds.expired and creds.refresh_token:
        try:
            print("Refreshing existing token...")
            creds.refresh(Request())
        except Exception as exc:
            print(f"Refresh failed ({exc}); starting a fresh authorization flow.")
            creds = None

    if not creds or not creds.valid:
        print("Opening browser for YouTube authorization...")
        flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_FILE), SCOPES)
        # prompt='consent' + access_type='offline' guarantees a refresh_token.
        creds = flow.run_local_server(
            port=0,
            access_type="offline",
            prompt="consent",
        )

    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    print(f"Saved token to {TOKEN_FILE}")

    # Confirm it works by reading the channel.
    try:
        from googleapiclient.discovery import build
        youtube = build("youtube", "v3", credentials=creds, cache_discovery=False)
        resp = youtube.channels().list(part="snippet", mine=True).execute()
        items = resp.get("items", [])
        if items:
            print(f"Authorized channel: {items[0]['snippet']['title']}")
        else:
            print("Authorized, but no channel found on this account.")
    except Exception as exc:
        print(f"Token saved, but verification call failed: {exc}")
        return 1

    print("Done. Auto-publish is ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
