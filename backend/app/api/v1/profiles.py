"""
Content profiles: what kind of channel this is.

Six presets ship with the app and a creator can add their own. Choosing one
changes which trend sources are scanned, how candidates are ranked, the voice
the script is written in, the visual vocabulary handed to the stock search, the
YouTube category and the publish schedule - without a redeploy.
"""
import logging

from fastapi import APIRouter, Body, HTTPException

from app.services import trend_sources
from app.services.profiles_service import store

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("")
async def list_profiles():
    """Every profile, plus which one is active and what source types exist."""
    return {
        "active": store.active_id(refresh=True),
        "profiles": store.list(),
        "source_types": trend_sources.AVAILABLE_SOURCES,
    }


@router.get("/{profile_id}")
async def get_profile(profile_id: str):
    profile = store.get(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"No such profile: {profile_id}")
    return profile


@router.post("/{profile_id}/activate")
async def activate_profile(profile_id: str):
    """Switch the channel over. Takes effect on the next run, and immediately
    for anything the dashboard previews."""
    try:
        profile = store.set_active(profile_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.error("Could not activate %s: %s", profile_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Could not switch profile.") from exc

    # The schedule lives in the profile, so the scheduler has to be rebuilt to
    # pick up new hours or a new timezone.
    try:
        from app.services import trends_scheduler
        trends_scheduler.restart_scheduler()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Profile activated but the scheduler did not restart: %s", exc)

    return {"active": profile_id, "profile": profile}


@router.post("")
async def create_profile(payload: dict = Body(...)):
    """Create or overwrite a custom profile."""
    try:
        return store.save_custom(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.error("Could not save profile: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Could not save the profile.") from exc


@router.delete("/{profile_id}")
async def delete_profile(profile_id: str):
    try:
        store.delete_custom(profile_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.error("Could not delete profile: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Could not delete the profile.") from exc
    return {"deleted": profile_id, "active": store.active_id(refresh=True)}
