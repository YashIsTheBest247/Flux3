"""
Bring-your-own-video ingest.

Upload a finished video; get back a thumbnail, captions, a title, a description,
tags, Shorts suggestions and - if publishing is on - a live YouTube URL.
"""
import logging
import tempfile
import threading
import uuid
from pathlib import Path

from fastapi import (APIRouter, BackgroundTasks, File, Form, HTTPException,
                     UploadFile)

from app.core.config import settings
from app.services import ingest_service

logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_SUFFIXES = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}

# One at a time. The render pipeline already serialises on an in-process lock
# for the same reason: a single worker on a small instance cannot run two
# ffmpeg jobs without one of them being OOM-killed.
_lock = threading.Lock()


@router.post("")
async def create_ingest(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    publish: bool = Form(default=False),
    privacy: str = Form(default=""),
    title: str = Form(default=""),
    suggest_clips: bool = Form(default=True),
):
    """Accept an upload and start processing it in the background."""
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix or 'unknown'}'. "
                   f"Accepted: {', '.join(sorted(ALLOWED_SUFFIXES))}.",
        )

    if _lock.locked():
        raise HTTPException(
            status_code=409,
            detail="Another video is being processed. This instance runs one at a time.",
        )

    job_id = uuid.uuid4().hex
    upload_dir = Path(tempfile.gettempdir()) / "flux-uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    target = upload_dir / f"{job_id}{suffix}"

    # Streamed to disk in chunks and size-checked as it arrives. Reading the
    # whole body into memory first would OOM a 512 MB instance on a file this
    # endpoint is otherwise happy to accept, and checking the length header
    # would trust a number the client chose.
    limit = settings.INGEST_MAX_MB * 1024 * 1024
    written = 0
    try:
        with target.open("wb") as handle:
            while chunk := await file.read(1024 * 1024):
                written += len(chunk)
                if written > limit:
                    handle.close()
                    target.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=413,
                        detail=f"That file is over the {settings.INGEST_MAX_MB} MB limit "
                               f"for this instance.",
                    )
                handle.write(chunk)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        target.unlink(missing_ok=True)
        logger.error("Upload failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Could not receive the upload.") from exc
    finally:
        await file.close()

    if written == 0:
        target.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="The uploaded file was empty.")

    job = ingest_service.IngestJob(job_id=job_id, filename=file.filename or target.name)
    ingest_service._register(job)  # noqa: SLF001 - same package

    options = {
        "publish": publish,
        "privacy": privacy or None,
        "title": title.strip() or None,
        "suggest_clips": suggest_clips,
    }
    background_tasks.add_task(_run, job, target, options)

    return {
        "job_id": job_id,
        "filename": job.filename,
        "size_bytes": written,
        "status_url": f"/api/v1/ingest/{job_id}",
    }


def _run(job: ingest_service.IngestJob, source: Path, options: dict) -> None:
    """Background entry point. Holds the single-job lock for the whole run."""
    if not _lock.acquire(blocking=False):
        job.error = "Another video started processing first. Try again shortly."
        job.stage, job.message = "error", job.error
        source.unlink(missing_ok=True)
        return
    try:
        ingest_service.process(job, source, options)
    except Exception:  # noqa: BLE001 - already recorded on the job
        logger.info("Ingest %s ended with an error.", job.job_id)
    finally:
        _lock.release()


@router.get("")
async def list_ingests():
    """Recent jobs, newest first. In-memory, so a restart clears them."""
    return {"jobs": ingest_service.recent_jobs(), "busy": _lock.locked(),
            "max_mb": settings.INGEST_MAX_MB}


@router.get("/{job_id}")
async def get_ingest(job_id: str):
    job = ingest_service.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=404,
            detail="No such job. Job state is held in memory, so a restart "
                   "clears it - if the video was published it is still on your channel.",
        )
    return job.to_dict()
