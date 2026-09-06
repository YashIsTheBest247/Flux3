"""
API v1 Router
"""
from fastapi import APIRouter

from app.api.v1 import connect, ingest, profiles, trends, videos

router = APIRouter()

router.include_router(videos.router, prefix="/videos", tags=["videos"])
router.include_router(trends.router, prefix="/trends", tags=["trends"])
router.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
router.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
# Mounted at /auth as well as /connect so the OAuth redirect URI reads as a
# sign-in path. Google matches the redirect literally, so this string is now
# part of the app's contract and must not be renamed casually.
router.include_router(connect.router, prefix="/connect", tags=["connect"])
router.include_router(connect.router, prefix="/auth", tags=["connect"])
