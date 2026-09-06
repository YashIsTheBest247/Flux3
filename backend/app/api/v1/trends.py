"""
Trending Pipeline API Endpoints

Read-only insight into the Economic Times trending pipeline plus a manual trigger.
The pipeline itself runs automatically on a schedule (see trends_scheduler).
"""
import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from app.services import trends_service
from app.services import trends_scheduler

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/status")
async def trends_status():
    """Scheduler status, next run time, and the last run's results."""
    return trends_scheduler.scheduler_status()


@router.get("/preview")
async def trends_preview(top_n: int = Query(10, ge=1, le=50)):
    """
    Preview the current ranked trending articles WITHOUT generating anything.
    Excludes articles already processed by the pipeline.
    """
    try:
        articles = trends_service.get_trending(top_n=top_n, exclude_processed=True)
        return {"count": len(articles), "articles": [a.to_dict() for a in articles]}
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Failed to build trends preview: {exc}", exc_info=True)
        raise HTTPException(status_code=502, detail=f"Failed to fetch trends: {exc}")


@router.post("/run")
async def trends_run_now(
    background_tasks: BackgroundTasks,
    top_n: int = Query(None, ge=1, le=20),
    auto_publish: bool = Query(None, description="Override TRENDS_AUTO_PUBLISH for this run"),
):
    """
    Trigger one pipeline run immediately (in the background). Generation still
    happens asynchronously; poll /trends/status for results.
    """
    background_tasks.add_task(trends_scheduler.run_pipeline_once, top_n, auto_publish)
    return {"success": True, "message": "Trending pipeline run triggered."}


@router.get("/sources")
async def trends_sources():
    """What the active profile is actually scanning, and what it found.

    Per-source counts rather than one merged number, because "the pipeline
    returned nothing" and "Reddit returned nothing" are different problems with
    different fixes, and the merged view hides which one you have.
    """
    from app.services import trend_sources
    from app.services.profiles_service import store

    profile = store.active()
    sources = profile.get("sources") or []
    report = []
    for spec in sources:
        kind = (spec.get("type") or "").lower()
        try:
            items = trend_sources.fetch_all([spec])
            report.append({
                "type": kind,
                "config": {k: v for k, v in spec.items() if k != "type"},
                "count": len(items),
                "sample": [a.title for a in items[:3]],
                "error": None,
            })
        except Exception as exc:  # noqa: BLE001
            report.append({"type": kind, "config": {}, "count": 0,
                           "sample": [], "error": str(exc)})

    return {
        "profile": {"id": profile.get("id"), "name": profile.get("name")},
        "sources": report,
        "available_types": trend_sources.AVAILABLE_SOURCES,
    }
