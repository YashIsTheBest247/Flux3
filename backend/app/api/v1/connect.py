"""
Connect: where finished videos get published.

By default they go to the channel this deployment owns, so a visitor can try
the whole pipeline without setting up a Google Cloud project. Turning that off
lets them connect their own channel instead, at which point uploads land on
their account and use their quota.

Model and stock-library keys are NOT here. They come from the environment: they
are the operator's cost centre and identical for every visitor, so a public
form asking for them was pointless and invited abuse.
"""
import logging

from fastapi import APIRouter, Body, HTTPException, Query
from fastapi.responses import HTMLResponse

from app.core.config import settings
from app.services import youtube_oauth
from app.services.credentials_service import vault

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/credentials")
async def get_credentials():
    """Field definitions plus what is configured. Never returns a secret value."""
    return vault.describe()


@router.put("/credentials")
async def put_credentials(updates: dict = Body(...)):
    """Save the fields the creator actually edited.

    Only keys present in the body are touched, so the dashboard can submit one
    changed field without the masked values of the others overwriting the real
    secrets behind them.
    """
    if not isinstance(updates, dict):
        raise HTTPException(status_code=400, detail="Expected a JSON object of field values.")
    try:
        vault.save(updates)
    except RuntimeError as exc:
        # Storage or key material missing - a configuration problem, not a bug.
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to save credentials: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Could not save the credentials.") from exc
    return vault.describe()


@router.get("/youtube")
async def youtube_status():
    """Connection state for the publishing card, including the redirect URI."""
    return youtube_oauth.status()


@router.get("/publishing")
async def get_publishing():
    """Where finished videos go, and whether each option is actually usable."""
    from app.services import youtube_service

    status = youtube_oauth.status()
    status["default_channel_title"] = settings.YOUTUBE_DEFAULT_CHANNEL_TITLE
    status["default_available"] = bool((settings.YOUTUBE_TOKEN_JSON or "").strip())
    status["mode"] = vault.publish_mode()
    status["readiness"] = youtube_service.readiness()
    # The OAuth client fields, flattened - this screen shows one group, so the
    # grouping in describe() is noise the client would only have to undo.
    described = vault.describe()
    status["fields"] = [f for group in described["groups"] for f in group["fields"]]
    status["storage_ready"] = described["storage_ready"]
    status["vault_error"] = described["error"]
    return status


@router.put("/publishing")
async def set_publishing(payload: dict = Body(...)):
    """Switch between the default channel and the visitor's own."""
    mode = str(payload.get("mode", "")).strip()
    try:
        vault.set_publish_mode(mode)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return await get_publishing()


@router.post("/youtube/start")
async def youtube_start():
    """Return the Google consent URL for the browser to open."""
    try:
        return youtube_oauth.start()
    except youtube_oauth.OAuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/youtube/callback", response_class=HTMLResponse)
async def youtube_callback(
    code: str = Query(default=""),
    state: str = Query(default=""),
    error: str = Query(default=""),
):
    """Where Google sends the browser back.

    Returns a small HTML page rather than JSON: a human is looking at this, and
    a raw JSON body in the address bar after clicking "Allow" reads as a crash
    even when everything worked.
    """
    if error:
        return _page(False, f"Google returned: {error}")
    if not code:
        return _page(False, "Google did not return an authorisation code.")
    try:
        result = youtube_oauth.finish(code, state)
    except youtube_oauth.OAuthError as exc:
        return _page(False, str(exc))
    except Exception as exc:  # noqa: BLE001
        logger.error("OAuth callback failed: %s", exc, exc_info=True)
        return _page(False, "Something went wrong completing the connection.")

    channel = (result.get("channel") or {}).get("title") or "your channel"
    return _page(True, f"Connected to {channel}.")


@router.post("/youtube/disconnect")
async def youtube_disconnect():
    """Revoke the token at Google and forget it here."""
    try:
        youtube_oauth.disconnect()
    except Exception as exc:  # noqa: BLE001
        logger.error("Disconnect failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Could not disconnect.") from exc
    return youtube_oauth.status()


def _page(ok: bool, message: str) -> HTMLResponse:
    """A self-contained result page.

    It closes itself if it was opened as a popup, and otherwise offers a link
    back - the same page has to work in both cases because whether the browser
    honoured window.open is not something the server gets to know.
    """
    accent = "#3FA97A" if ok else "#D06A5A"
    heading = "Channel connected" if ok else "Could not connect"
    html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{heading}</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  body {{ margin:0; min-height:100vh; display:grid; place-items:center;
         background:#12100E; color:#F2EDE4; font:16px/1.6 ui-sans-serif,system-ui,sans-serif; }}
  .card {{ max-width:30rem; padding:2.5rem; text-align:center; }}
  .dot  {{ width:.75rem; height:.75rem; border-radius:99px; background:{accent};
           display:inline-block; margin-bottom:1.25rem; }}
  h1 {{ font:400 1.75rem/1.2 ui-serif,Georgia,serif; margin:0 0 .5rem; }}
  p  {{ color:#A79B88; margin:0 0 2rem; }}
  a  {{ color:#F2EDE4; text-decoration:none; border:1px solid #3A342C;
        padding:.6rem 1.25rem; border-radius:99px; font-size:.875rem; }}
  a:hover {{ background:#1C1916; }}
</style></head>
<body><div class="card">
  <span class="dot"></span>
  <h1>{heading}</h1>
  <p>{message}</p>
  <a href="/">Back to Flux</a>
</div>
<script>
  // Opened as a popup: tell the dashboard to refresh, then get out of the way.
  if (window.opener) {{
    try {{ window.opener.postMessage({{ source: 'flux-youtube-oauth', ok: {str(ok).lower()} }}, '*'); }} catch (e) {{}}
    setTimeout(function () {{ window.close(); }}, 1200);
  }}
</script>
</body></html>"""
    return HTMLResponse(content=html, status_code=200)
