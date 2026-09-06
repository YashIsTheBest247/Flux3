"""
Video Generation Service
Orchestrates the entire video generation pipeline
All paths are dynamically resolved from configuration
"""
import logging
import json
import time
import re
import shutil
from pathlib import Path
from fastapi import BackgroundTasks

from app.schemas.video import VideoGenerationRequest, VideoGenerationResponse
from app.core.config import settings
from imagegen.generate_script import VideoScriptGenerator
from imagegen.gen_img import main_generate_images
from tts.generate_audio_refactored import main_generate_audio
from assembly.scripts.assembly_video_refactored import create_video, create_complete_srt

logger = logging.getLogger(__name__)


class VideoGenerationService:
    """Service for generating videos"""
    
    def __init__(self):
        self.script_generator = VideoScriptGenerator(
            api_key=settings.GEMINI_API_KEY,
            model=settings.GEMINI_TEXT_MODEL,
        )
    
    def _clean_directory(self, folder_path: Path):
        """Clean all files in a directory"""
        if not folder_path.exists():
            return
        
        for item in folder_path.iterdir():
            try:
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            except Exception as e:
                logger.warning(f"Failed to delete {item}: {e}")
    
    def _generate_video_filename(self, topic: str) -> str:
        """Generate a clean filename from topic"""
        clean_topic = re.sub(r"[^A-Za-z0-9]", "_", topic)[:30]
        timestamp = int(time.time())
        return f"{clean_topic}_{timestamp}.mp4"
    
    async def generate_video_async(
        self,
        request: VideoGenerationRequest,
        background_tasks: BackgroundTasks
    ) -> VideoGenerationResponse:
        """
        Generate video asynchronously
        Returns immediately with success status, actual generation happens in background
        """
        try:
            # Generate video filename
            video_filename = self._generate_video_filename(request.topic)
            
            # Add background task
            background_tasks.add_task(
                self._generate_video_task,
                request,
                video_filename
            )
            
            return VideoGenerationResponse(
                success=True,
                message="Video generation started. This may take several minutes.",
                video_path=f"/static/videos/{video_filename}",
                video_filename=video_filename
            )
            
        except Exception as e:
            logger.error(f"Failed to start video generation: {str(e)}", exc_info=True)
            return VideoGenerationResponse(
                success=False,
                message="Failed to start video generation",
                error=str(e)
            )
    
    def _generate_video_task(self, request: VideoGenerationRequest, video_filename: str):
        """
        Background task for video generation
        This is the main pipeline that orchestrates all steps
        All paths are dynamically resolved from configuration
        """
        try:
            logger.info(f"Starting video generation for: {request.topic}")
            
            # Step 1: Clean working directories
            logger.info("Cleaning working directories...")
            self._clean_directory(settings.IMAGES_DIR)
            self._clean_directory(settings.AUDIO_DIR)
            
            # Step 2: Generate script
            logger.info("Generating script...")
            script = self.script_generator.generate_script(
                topic=request.topic,
                duration=request.duration,
                key_points=request.key_points if request.key_points else None
            )
            
            # Save script
            script_path = settings.SCRIPT_DIR / "script.json"
            script_path.parent.mkdir(parents=True, exist_ok=True)
            self.script_generator.save_script(script, str(script_path))
            logger.info(f"Script saved to: {script_path}")
            
            # Step 3: Generate images
            logger.info("Generating images...")
            main_generate_images(
                script_path=script_path,
                images_output_path=settings.IMAGES_DIR,
                gemini_api_key=settings.GEMINI_API_KEY,
                pexels_api_key=settings.PEXELS_API_KEY,
                delay_seconds=settings.IMAGE_GEN_DELAY,
                gemini_model=settings.IMAGE_GEN_MODEL,
                aspect_ratio=settings.IMAGE_ASPECT_RATIO,
            )
            logger.info("Images generated successfully")
            
            # Step 4: Generate audio
            logger.info("Generating audio...")
            main_generate_audio(
                script_path=script_path,
                audio_path=settings.AUDIO_DIR
            )
            logger.info("Audio generated successfully")
            
            # Step 5: Generate subtitles
            logger.info("Generating subtitles...")
            clean_topic = re.sub(r"[^A-Za-z0-9]", "_", request.topic)[:30]
            srt_path = settings.SUBTITLE_OUTPUT_DIR / f"{clean_topic}.srt"
            create_complete_srt(
                script_folder=script_path,
                audio_file_folder=settings.AUDIO_DIR,
                outfile_path=srt_path,
                chunk_size=settings.DEFAULT_CHUNK_SIZE
            )
            logger.info(f"Subtitles saved to: {srt_path}")
            
            # Step 6: Assemble video
            logger.info("Assembling video...")
            temp_video_path = settings.VIDEO_OUTPUT_DIR / video_filename
            
            create_video(
                image_folder=settings.IMAGES_DIR,
                audio_folder=settings.AUDIO_DIR,
                script_path=script_path,
                font_path=settings.FONT_PATH,
                output_file=temp_video_path,
                intro_image_path=settings.INTRO_IMAGE_PATH,
                with_subtitles=True,
                fps=settings.DEFAULT_VIDEO_FPS
            )
            
            # Step 7: Copy to static directory
            final_video_path = settings.STATIC_DIR / "videos" / video_filename
            final_video_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(temp_video_path, final_video_path)

            logger.info(f"Video generation complete: {video_filename}")

            # Step 8: Auto-publish to YouTube (only when the user enabled it)
            if request.publish_to_youtube:
                self._publish_to_youtube(request, final_video_path)

        except Exception as e:
            logger.error(f"Video generation task failed: {str(e)}", exc_info=True)
            raise

    def _publish_to_youtube(self, request: VideoGenerationRequest, video_path: Path):
        """
        Upload the finished video to YouTube. Failures here are logged but do not
        fail the whole generation task — the video is already rendered and saved.
        """
        # Imported lazily so the rest of the pipeline runs even if the YouTube
        # client libraries aren't installed.
        from app.services.youtube_service import upload_video, YouTubeServiceError

        try:
            logger.info("Publishing video to YouTube...")
            title = request.topic.strip()[:100]
            description_parts = [f"{request.topic.strip()}\n"]
            if request.key_points:
                description_parts.append("In this video:")
                description_parts.extend(f"- {point}" for point in request.key_points)
            description_parts.append("\nGenerated with Flux.")
            description = "\n".join(description_parts)

            result = upload_video(
                file_path=video_path,
                title=title,
                description=description,
            )
            logger.info(f"Published to YouTube: {result['url']}")
        except YouTubeServiceError as e:
            logger.error(f"YouTube publishing failed: {e}")
        except Exception as e:  # noqa: BLE001
            logger.error(f"Unexpected error while publishing to YouTube: {e}", exc_info=True)
