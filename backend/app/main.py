"""
FastAPI Video Generator - Main Application Entry Point
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
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
    
    yield
    
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


@app.get("/")
async def root():
    """API root - the UI is served by the separate frontend app"""
    return {
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "api": "/api/v1",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
