"""
YouTube OAuth, done in the browser.

The original flow was `python authorize_youtube.py` on a laptop, which is fine
for the person who wrote the app and useless for anyone else. This module runs
the same OAuth dance from the dashboard: the creator pastes the client ID and
secret from their own Google Cloud project, clicks Connect, approves on
Google's screen, and lands back on the dashboard with their channel connected.

Their own project matters. The upload goes to their channel, the daily quota is
theirs, and this deployment never holds a credential that can touch anyone
else's account.

Implemented against the raw token endpoint with `requests` rather than
google-auth-oauthlib. The library wants to own the redirect and run a local
server; here FastAPI already owns the redirect, so the library would only be
wrapping one HTTP POST.
"""
import json
import logging
import secrets
import time
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlencode

import requests

from app.core.config import settings
from app.services.credentials_service import vault

logger = logging.getLogger(__name__)

AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
REVOKE_ENDPOINT = "https://oauth2.googleapis.com/revoke"

# youtube.upload publishes the video; force-ssl covers setting a thumbnail,
# uploading a caption track and (later) reading comments. Both are needed -
# an upload-only token fails on thumbnails.set with a bare 403.
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]

CALLBACK_PATH = "/api/v1/auth/youtube/callback"

# CSRF state, held in memory. A restart between "Connect" and the redirect back
# loses it and the creator has to click Connect again - which is the correct
# failure, and cheaper than a database row for a value that lives 60 seconds.
_pending_state: Dict[str, float] = {}
_STATE_TTL_SECONDS = 900


class OAuthError(RuntimeError):
    """Raised when the OAuth flow cannot proceed. Message is shown to the user."""


def _client_pair() -> Tuple[str, str]:
    client_id = (vault.get("YOUTUBE_CLIENT_ID") or settings.YOUTUBE_CLIENT_ID or "").strip()
    client_secret = (
        vault.get("YOUTUBE_CLIENT_SECRET") or settings.YOUTUBE_CLIENT_SECRET or ""
    ).strip()
    if not client_id or not client_secret:
        raise OAuthError(
            "Add your Google OAuth client ID and secret first - they are on the "
            "Connect screen, under YouTube."
        )
    return client_id, client_secret


def redirect_uri() -> str:
    """The exact string that must also be registered in Google Cloud.

    Google compares this character for character. A trailing slash, http vs
    https, or a different host is a `redirect_uri_mismatch`, which is the single
    most common way this flow fails.
    """
    base = settings.public_base_url
    if not base:
        # Local development. Whatever port uvicorn is on is what Google has to
        # be told about, so build it from the configured port rather than
        # guessing 8000.
        base = f"http://localhost:{settings.PORT}"
    return f"{base}{CALLBACK_PATH}"


def _prune_state() -> None:
    cutoff = time.time() - _STATE_TTL_SECONDS
    for key in [k for k, created in _pending_state.items() if created < cutoff]:
        _pending_state.pop(key, None)


def start() -> Dict[str, str]:
    """Build the Google consent URL the browser should be sent to."""
    client_id, _ = _client_pair()
    _prune_state()
    state = secrets.token_urlsafe(24)
    _pending_state[state] = time.time()

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri(),
        "response_type": "code",
        "scope": " ".join(SCOPES),
        # offline + consent is what actually returns a refresh_token. Without
        # `prompt=consent` Google omits it on every authorisation after the
        # first, and the connection silently dies an hour later when the access
        # token expires with nothing to refresh from.
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
        "state": state,
    }
    return {
        "authorize_url": f"{AUTH_ENDPOINT}?{urlencode(params)}",
        "redirect_uri": redirect_uri(),
        "state": state,
    }


def finish(code: str, state: str) -> Dict[str, Any]:
    """Exchange the authorisation code and store the token in the vault."""
    _prune_state()
    if state not in _pending_state:
        raise OAuthError(
            "This sign-in link has expired or was not started here. Click "
            "Connect again."
        )
    _pending_state.pop(state, None)

    client_id, client_secret = _client_pair()
    response = requests.post(
        TOKEN_ENDPOINT,
        data={
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri(),
            "grant_type": "authorization_code",
        },
        timeout=30,
    )
    if not response.ok:
        detail = _google_error(response)
        if "redirect_uri_mismatch" in detail:
            detail = (
                f"redirect_uri_mismatch. Add exactly this URI to your OAuth "
                f"client in Google Cloud: {redirect_uri()}"
            )
        raise OAuthError(f"Google rejected the sign-in: {detail}")

    payload = response.json()
    refresh_token = payload.get("refresh_token")
    if not refresh_token:
        raise OAuthError(
            "Google did not return a refresh token, so the connection would "
            "stop working within the hour. Remove this app at "
            "myaccount.google.com/permissions and connect again."
        )

    token_info = {
        "token": payload.get("access_token"),
        "refresh_token": refresh_token,
        "token_uri": TOKEN_ENDPOINT,
        "client_id": client_id,
        "client_secret": client_secret,
        "scopes": SCOPES,
    }

    updates: Dict[str, str] = {"YOUTUBE_TOKEN_JSON": json.dumps(token_info)}
    # Store it before asking who they are: if the channel lookup fails the
    # connection is still good, and losing a working token over a cosmetic
    # lookup would be absurd.
    vault.save(updates)

    channel = _fetch_channel(payload.get("access_token"))
    if channel:
        vault.save({
            "YOUTUBE_CHANNEL_TITLE": channel.get("title", ""),
            "YOUTUBE_CHANNEL_ID": channel.get("id", ""),
        })

    logger.info("YouTube connected: %s", channel.get("title") if channel else "channel unknown")
    return {"connected": True, "channel": channel}


def _fetch_channel(access_token: Optional[str]) -> Optional[Dict[str, str]]:
    """Who did we just connect? Best effort - a failure here is cosmetic."""
    if not access_token:
        return None
    try:
        response = requests.get(
            "https://www.googleapis.com/youtube/v3/channels",
            params={"part": "snippet", "mine": "true"},
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=20,
        )
        if not response.ok:
            logger.warning("Channel lookup failed: %s", _google_error(response))
            return None
        items = response.json().get("items") or []
        if not items:
            return None
        snippet = items[0].get("snippet", {})
        thumbs = snippet.get("thumbnails", {})
        return {
            "id": items[0].get("id", ""),
            "title": snippet.get("title", ""),
            "thumbnail": (thumbs.get("default") or {}).get("url", ""),
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("Channel lookup failed: %s", exc)
        return None


def disconnect() -> None:
    """Revoke the token at Google, then forget it locally.

    Revoking first matters: dropping our copy without telling Google would
    leave this app listed on the creator's account with nothing here able to
    withdraw it.
    """
    token_json = vault.get("YOUTUBE_TOKEN_JSON")
    if token_json:
        try:
            data = json.loads(token_json)
            requests.post(
                REVOKE_ENDPOINT,
                data={"token": data.get("refresh_token") or data.get("token")},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=15,
            )
        except Exception as exc:  # noqa: BLE001
            # Already-revoked tokens 400 here. Either way the local clear below
            # is what the creator asked for, so never block on this.
            logger.info("Token revoke returned an error (continuing): %s", exc)
    vault.clear(["YOUTUBE_TOKEN_JSON", "YOUTUBE_CHANNEL_TITLE", "YOUTUBE_CHANNEL_ID"])


def status() -> Dict[str, Any]:
    """What the Connect screen shows for the YouTube card."""
    data = vault.all()
    client_id = (data.get("YOUTUBE_CLIENT_ID") or settings.YOUTUBE_CLIENT_ID or "").strip()
    client_secret = (
        data.get("YOUTUBE_CLIENT_SECRET") or settings.YOUTUBE_CLIENT_SECRET or ""
    ).strip()
    token = (data.get("YOUTUBE_TOKEN_JSON") or settings.YOUTUBE_TOKEN_JSON or "").strip()
    return {
        "client_configured": bool(client_id and client_secret),
        "connected": bool(token),
        "channel_title": data.get("YOUTUBE_CHANNEL_TITLE", ""),
        "channel_id": data.get("YOUTUBE_CHANNEL_ID", ""),
        "redirect_uri": redirect_uri(),
        "scopes": SCOPES,
    }


def _google_error(response: requests.Response) -> str:
    try:
        body = response.json()
        return (
            body.get("error_description")
            or body.get("error", {}).get("message")
            or (body.get("error") if isinstance(body.get("error"), str) else "")
            or response.text[:300]
        )
    except Exception:  # noqa: BLE001
        return response.text[:300]
