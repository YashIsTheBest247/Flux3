"""
FastAPI Video Generator - Main Application Entry Point
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1 import router as api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(settings.LOG_FILE)
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("Starting FastAPI Video Generator...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")

    # Ensure required directories exist
    settings.ensure_directories()

    # Pull the dashboard-entered credentials in BEFORE anything reads a key.
    # Without this the scheduler, the storage client and the script model all
    # boot against the environment alone and a creator who configured
    # everything through the UI would see an unconfigured app until the next
    # restart.
    try:
        from app.services.credentials_service import vault
        vault.apply_to_settings()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not load stored credentials: %s", exc)

    from app.services.profiles_service import store as profiles_store
    logger.info("Active content profile: %s", profiles_store.active_id())

    # Start the trending pipeline scheduler (no-op unless TRENDS_ENABLED=true)
    from app.services.trends_scheduler import start_scheduler, shutdown_scheduler
    start_scheduler()

    # Keep the Render instance from idling out between scheduled runs.
    from app.services.keepalive import start_keepalive, shutdown_keepalive
    start_keepalive()

    yield

    shutdown_keepalive()
    shutdown_scheduler()
    logger.info("Shutting down FastAPI Video Generator...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered educational video generation service",
    version=settings.VERSION,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")

# Include API routes
app.include_router(api_router, prefix="/api/v1")


# Built single-page app, when it has been bundled into the image. Serving the UI
# from the same origin as the API gives deployments ONE public URL and removes
# CORS from the equation entirely; the split Vercel + API deploy still works when
# this directory is absent.
SPA_DIR = settings.STATIC_DIR / "app"
SPA_INDEX = SPA_DIR / "index.html"


@app.get("/")
async def root():
    """Serve the bundled UI when present, otherwise describe the API."""
    if SPA_INDEX.exists():
        return FileResponse(SPA_INDEX)
    return {
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "api": "/api/v1",
    }


@app.get("/ping")
async def ping():
    """Liveness beacon for the keep-alive pinger.

    Separate from /health on purpose. /health reaches out to Backblaze and
    YouTube on every call; at a ping every 12 minutes that is ~120 needless
    round trips a day. Keeping the instance awake only requires that a request
    arrive, so this one touches nothing.
    """
    return {"ok": True}


@app.get("/health")
async def health_check():
    """
    Health check + readiness report.

    Always returns 200 so the platform's health probe passes even when an
    optional integration is unconfigured — `ready` tells you whether the app can
    actually render, and `checks` says exactly what is missing.
    """
    from app.services import youtube_service
    from app.services.genblaze_service import genblaze
    from app.services.keepalive import keepalive_status
    from app.services.profiles_service import store as profiles_store
    from app.services.storage_service import storage

    b2 = storage.status()
    youtube = youtube_service.readiness()
    checks = {
        "script_llm": bool(settings.GEMINI_API_KEY) or settings.SCRIPT_PROVIDER == "ollama",
        "backblaze_b2": b2["available"],
        "genblaze": genblaze.enabled,
        "genblaze_sink": genblaze.status()["sink"] is not None,
        "stock_images": bool(settings.PEXELS_API_KEY),
        "gmi_cloud": settings.gmi_configured,
        "youtube_publishing": youtube["ready"],
    }
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        # Renders need a script model; everything else degrades gracefully.
        "ready": checks["script_llm"],
        "durable_storage": checks["backblaze_b2"],
        "checks": checks,
        "backblaze_b2": b2,
        "genblaze": genblaze.status(),
        "youtube": youtube,
        "keepalive": keepalive_status(),
        "profile": {
            "active": profiles_store.active_id(),
            "name": profiles_store.active().get("name"),
        },
    }


# Mounted LAST so /health, /docs and /api/v1/* keep priority — this only catches
# the SPA's own asset requests (/assets/*, /favicon.svg, ...).
if SPA_DIR.exists():
    app.mount("/", StaticFiles(directory=SPA_DIR, html=True), name="spa")
    logger.info("Serving bundled UI from %s", SPA_DIR)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
