"""
Application Configuration
Loads all settings from environment variables
"""
import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

# Load .env file explicitly
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "Flux Video Generator"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    
    # CORS (includes the Vite dev server origins used by the frontend)
    CORS_ORIGINS: str = Field(
        default="http://localhost:8000,http://127.0.0.1:8000,http://localhost:5173,http://127.0.0.1:5173",
        env="CORS_ORIGINS"
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS string into list"""
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        return self.CORS_ORIGINS
    
    # API Keys
    GEMINI_API_KEY: str = Field(..., env="GEMINI_API_KEY")

    # Pexels API key - primary source for scene images (optional; falls back to Gemini)
    PEXELS_API_KEY: str = Field(default="", env="PEXELS_API_KEY")

    # Gemini text generation model
    GEMINI_TEXT_MODEL: str = Field(default="gemini-2.5-flash", env="GEMINI_TEXT_MODEL")
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    UPLOAD_FOLDER: Optional[Path] = Field(default=None)
    STATIC_DIR: Optional[Path] = Field(default=None)
    RESOURCE_DIR: Optional[Path] = Field(default=None)
    
    # Resource subdirectories
    SCRIPT_DIR: Optional[Path] = Field(default=None)
    IMAGES_DIR: Optional[Path] = Field(default=None)
    AUDIO_DIR: Optional[Path] = Field(default=None)
    VIDEO_OUTPUT_DIR: Optional[Path] = Field(default=None)
    SUBTITLE_OUTPUT_DIR: Optional[Path] = Field(default=None)
    FONT_PATH: Optional[Path] = Field(default=None)
    INTRO_IMAGE_PATH: Optional[Path] = Field(default=None)
    
    # File upload limits
    MAX_UPLOAD_SIZE: int = Field(default=50 * 1024 * 1024, env="MAX_UPLOAD_SIZE")  # 50MB
    
    # Video generation settings
    DEFAULT_VIDEO_DURATION: int = Field(default=60, env="DEFAULT_VIDEO_DURATION")
    DEFAULT_VIDEO_FPS: int = Field(default=24, env="DEFAULT_VIDEO_FPS")
    DEFAULT_CHUNK_SIZE: int = Field(default=10, env="DEFAULT_CHUNK_SIZE")
    
    # Image settings - Pexels primary, Gemini fallback
    IMAGE_GEN_MODEL: str = Field(default="gemini-2.5-flash-image", env="IMAGE_GEN_MODEL")
    IMAGE_ASPECT_RATIO: str = Field(default="1:1", env="IMAGE_ASPECT_RATIO")
    
    # TTS settings
    TTS_LANG_CODE: str = Field(default="b", env="TTS_LANG_CODE")
    
    # Logging
    LOG_FILE: str = Field(default="app.log", env="LOG_FILE")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Background task settings
    TASK_TIMEOUT: int = Field(default=600, env="TASK_TIMEOUT")  # 10 minutes
    IMAGE_GEN_DELAY: float = Field(default=2.0, env="IMAGE_GEN_DELAY")  # Delay between image gen calls
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore"
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Initialize paths after base initialization
        if self.UPLOAD_FOLDER is None:
            self.UPLOAD_FOLDER = self.BASE_DIR / "uploads"
        
        if self.STATIC_DIR is None:
            self.STATIC_DIR = self.BASE_DIR / "static"

        if self.RESOURCE_DIR is None:
            self.RESOURCE_DIR = self.BASE_DIR / "resources"
        
        # Resource subdirectories
        if self.SCRIPT_DIR is None:
            self.SCRIPT_DIR = self.RESOURCE_DIR / "scripts"
        
        if self.IMAGES_DIR is None:
            self.IMAGES_DIR = self.RESOURCE_DIR / "images"
        
        if self.AUDIO_DIR is None:
            self.AUDIO_DIR = self.RESOURCE_DIR / "audio"
        
        if self.VIDEO_OUTPUT_DIR is None:
            self.VIDEO_OUTPUT_DIR = self.RESOURCE_DIR / "video"
        
        if self.SUBTITLE_OUTPUT_DIR is None:
            self.SUBTITLE_OUTPUT_DIR = self.RESOURCE_DIR / "subtitles"
        
        if self.FONT_PATH is None:
            self.FONT_PATH = self.RESOURCE_DIR / "font" / "font.ttf"
        
        if self.INTRO_IMAGE_PATH is None:
            self.INTRO_IMAGE_PATH = self.RESOURCE_DIR / "intro" / "intro.jpg"
    
    def ensure_directories(self):
        """Ensure all required directories exist"""
        directories = [
            self.UPLOAD_FOLDER,
            self.STATIC_DIR / "videos",
            self.RESOURCE_DIR,
            self.SCRIPT_DIR,
            self.IMAGES_DIR,
            self.AUDIO_DIR,
            self.VIDEO_OUTPUT_DIR,
            self.SUBTITLE_OUTPUT_DIR,
            self.RESOURCE_DIR / "font",
            self.RESOURCE_DIR / "intro"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


# Create global settings instance
settings = Settings()
