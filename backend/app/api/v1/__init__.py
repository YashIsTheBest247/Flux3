"""
API v1 Router
"""
from fastapi import APIRouter
from app.api.v1 import videos, upload

router = APIRouter()

router.include_router(videos.router, prefix="/videos", tags=["videos"])
router.include_router(upload.router, prefix="/upload", tags=["upload"])
