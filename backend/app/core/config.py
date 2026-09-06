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

    # YouTube auto-publishing
    # When true, EVERY generated video is published (not just ones where the UI
    # toggle/publish_to_youtube flag is set). The UI toggle can still enable
    # publishing per-render even when this is false.
    YOUTUBE_AUTO_UPLOAD: bool = Field(default=False, env="YOUTUBE_AUTO_UPLOAD")
    YOUTUBE_PRIVACY_STATUS: str = Field(default="private", env="YOUTUBE_PRIVACY_STATUS")
    YOUTUBE_CATEGORY_ID: str = Field(default="27", env="YOUTUBE_CATEGORY_ID")  # 27 = Education
    YOUTUBE_DEFAULT_TAGS: str = Field(default="education,flux,ai", env="YOUTUBE_DEFAULT_TAGS")
    SECRETS_DIR: Optional[Path] = Field(default=None)
    YOUTUBE_CLIENT_SECRET_FILE: Optional[Path] = Field(default=None)
    YOUTUBE_TOKEN_FILE: Optional[Path] = Field(default=None)
    # Deployment fallback: paste the contents of youtube_token.json here when the
    # filesystem is ephemeral/read-only (e.g. Render). Takes priority over the file.
    YOUTUBE_TOKEN_JSON: str = Field(default="", env="YOUTUBE_TOKEN_JSON")

    @property
    def youtube_tags_list(self) -> List[str]:
        """Parse YOUTUBE_DEFAULT_TAGS into a list"""
        return [tag.strip() for tag in self.YOUTUBE_DEFAULT_TAGS.split(",") if tag.strip()]

    # Trending pipeline (Economic Times RSS -> rank -> short-form video)
    # Disabled by default: enabling starts a background scheduler that consumes
    # the Gemini quota and (optionally) uploads to YouTube unattended.
    TRENDS_ENABLED: bool = Field(default=False, env="TRENDS_ENABLED")
    TRENDS_FEED_URLS: str = Field(
        default=(
            "https://economictimes.indiatimes.com/rssfeedstopstories.cms,"
            "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms,"
            "https://economictimes.indiatimes.com/industry/rssfeeds/13352306.cms,"
            "https://economictimes.indiatimes.com/news/economy/rssfeeds/1373380680.cms,"
            "https://economictimes.indiatimes.com/tech/rssfeeds/13357270.cms"
        ),
        env="TRENDS_FEED_URLS",
    )
    TRENDS_INTERVAL_HOURS: float = Field(default=6.0, env="TRENDS_INTERVAL_HOURS")
    TRENDS_TOP_N: int = Field(default=3, env="TRENDS_TOP_N")
    TRENDS_VIDEO_DURATION: int = Field(default=60, env="TRENDS_VIDEO_DURATION")
    TRENDS_MAX_AGE_HOURS: float = Field(default=24.0, env="TRENDS_MAX_AGE_HOURS")
    TRENDS_AUTO_PUBLISH: bool = Field(default=False, env="TRENDS_AUTO_PUBLISH")
    TRENDS_RUN_ON_STARTUP: bool = Field(default=False, env="TRENDS_RUN_ON_STARTUP")
    TRENDS_STATE_FILE: Optional[Path] = Field(default=None)

    @property
    def trends_feed_urls_list(self) -> List[str]:
        """Parse TRENDS_FEED_URLS into a list"""
        return [url.strip() for url in self.TRENDS_FEED_URLS.split(",") if url.strip()]
    
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

        # Secrets (YouTube OAuth credentials)
        if self.SECRETS_DIR is None:
            self.SECRETS_DIR = self.BASE_DIR / "secrets"

        if self.YOUTUBE_CLIENT_SECRET_FILE is None:
            self.YOUTUBE_CLIENT_SECRET_FILE = self.SECRETS_DIR / "youtube_client_secret.json"

        if self.YOUTUBE_TOKEN_FILE is None:
            self.YOUTUBE_TOKEN_FILE = self.SECRETS_DIR / "youtube_token.json"

        # Trending pipeline state (processed article links, for dedup)
        if self.TRENDS_STATE_FILE is None:
            self.TRENDS_STATE_FILE = self.RESOURCE_DIR / "trends_state.json"
        
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
