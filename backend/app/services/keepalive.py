"""
Keep-alive self-ping.

Render spins a free/starter web service down after roughly 15 minutes without
inbound traffic, and waking it costs the better part of a minute — long enough
that a judge clicking the demo link sees a blank page first. A request every
KEEPALIVE_MINUTES (default 12) keeps the instance warm.

Two things worth knowing about this file:

1. **A self-ping cannot wake a sleeping instance.** Once Render stops the
   container nothing inside it runs, including this scheduler. So this is the
   backstop, not the defence — `.github/workflows/keepalive.yml` pings from
   outside and is what actually revives the service after a deploy or a crash.

2. **It pings during renders too.** A render takes minutes and generates no
   inbound traffic of its own, so that is precisely the window in which an
   idle-timeout would fire. The request is a bare `/ping` and costs nothing.
"""
import logging
from typing import Optional

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings

logger = logging.getLogger(__name__)

JOB_ID = "keepalive_ping"
_scheduler: Optional[BackgroundScheduler] = None

# Short by design. If the instance is busy assembling a video the ping may sit
# in the queue, and a ping that has not landed within 30s has already done its
# job of proving the service is reachable — or has failed in a way retrying
# inside the same tick would not fix.
_TIMEOUT_SECONDS = 30


def ping_once() -> bool:
    """Hit the service's own public URL. Never raises — a failed ping is a log
    line, not an outage, and the next tick is only minutes away."""
    url = settings.keepalive_target
    if not url:
        return False
    try:
        response = requests.get(url, timeout=_TIMEOUT_SECONDS)
        logger.debug("Keep-alive ping %s -> %s", url, response.status_code)
        return response.ok
    except Exception as exc:
        logger.warning("Keep-alive ping to %s failed: %s", url, exc)
        return False


def start_keepalive() -> None:
    """Start the self-ping loop, unless disabled or there is no URL to ping."""
    global _scheduler

    if not settings.KEEPALIVE_ENABLED:
        logger.info("Keep-alive disabled (KEEPALIVE_ENABLED=false).")
        return

    if _scheduler and _scheduler.running:
        logger.info("Keep-alive already running.")
        return

    url = settings.keepalive_target
    if not url:
        # Local development, or a host that does not advertise its own URL.
        # Nothing is wrong; there is simply nothing to keep awake.
        logger.info(
            "Keep-alive idle: no public URL known. Render sets "
            "RENDER_EXTERNAL_URL automatically; elsewhere set KEEPALIVE_URL."
        )
        return

    minutes = max(1.0, float(settings.KEEPALIVE_MINUTES))
    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(
        ping_once,
        trigger=IntervalTrigger(minutes=minutes),
        id=JOB_ID,
        max_instances=1,
        # A ping that was missed while the process was busy is worthless after
        # the fact — the next one is what matters.
        coalesce=True,
        misfire_grace_time=60,
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("Keep-alive started: %s every %g minute(s).", url, minutes)


def shutdown_keepalive() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Keep-alive stopped.")
    _scheduler = None


def keepalive_status() -> dict:
    running = bool(_scheduler and _scheduler.running)
    next_run = None
    if running:
        job = _scheduler.get_job(JOB_ID)
        if job and job.next_run_time:
            next_run = job.next_run_time.isoformat()
    return {
        "enabled": settings.KEEPALIVE_ENABLED,
        "running": running,
        "target": settings.keepalive_target,
        "interval_minutes": settings.KEEPALIVE_MINUTES,
        "next_ping_at": next_run,
    }
