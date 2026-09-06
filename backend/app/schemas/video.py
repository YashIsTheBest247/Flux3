"""
Video Generation Request/Response Models
"""
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class VideoGenerationRequest(BaseModel):
    """Request model for video generation"""
    topic: str = Field(..., description="The topic of the video", min_length=1, max_length=200)
    duration: int = Field(default=60, description="Duration in seconds", ge=10, le=300)
    key_points: List[str] = Field(default=[], description="Key points to cover in the video")
    style: str = Field(default="educational", description="Video style")
    publish_to_youtube: bool = Field(
        default=False,
        description="When true, the finished video is auto-published to YouTube."
    )
    privacy_status: Literal["unlisted", "public", "private"] = Field(
        default="unlisted",
        description="YouTube visibility for the published video."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Introduction to Machine Learning",
                "duration": 60,
                "key_points": [
                    "What is machine learning",
                    "Types of machine learning",
                    "Real-world applications"
                ],
                "style": "educational",
                "publish_to_youtube": False
            }
        }


class VideoGenerationResponse(BaseModel):
    """Response model for video generation"""
    success: bool
    message: str
    video_path: Optional[str] = None
    video_filename: Optional[str] = None
    youtube_url: Optional[str] = None
    error: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Video generated successfully",
                "video_path": "/static/videos/introduction_to_machine_learning_1234567890.mp4",
                "video_filename": "introduction_to_machine_learning_1234567890.mp4"
            }
        }


class VideoListResponse(BaseModel):
    """Response model for video listing"""
    name: str
    path: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "introduction_to_machine_learning_1234567890.mp4",
                "path": "/static/videos/introduction_to_machine_learning_1234567890.mp4"
            }
        }
