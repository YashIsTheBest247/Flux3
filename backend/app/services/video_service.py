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
import subprocess
from pathlib import Path
from typing import Optional
from fastapi import BackgroundTasks

from app.schemas.video import VideoGenerationRequest, VideoGenerationResponse
from app.core.config import settings
from imagegen.generate_script import VideoScriptGenerator
# NOTE: the image/TTS/assembly pipeline (which pulls in torch, kokoro, moviepy,
# opencv) is imported lazily inside _generate_video_task — NOT at module import.
# This keeps the web process light at boot so the API/health/trends endpoints
# survive on small (e.g. 512 MB free-tier) instances; the heavy deps are only
# loaded when an actual render runs in the background.

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

            # Lazy imports: load the heavy pipeline only when actually rendering.
            from imagegen.gen_img import main_generate_images
            from tts.generate_audio_refactored import main_generate_audio
            from assembly.scripts.assembly_video_refactored import (
                create_video,
                create_complete_srt,
            )

            # Cap CPU threads to keep peak memory down on small instances.
            try:
                import torch
                torch.set_num_threads(1)
            except Exception:  # noqa: BLE001 - torch optional / best-effort
                pass

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
            
            # Step 3: Source images.
            # Podcast = one cover image held for the whole episode.
            # Video   = a distinct image per scene (Pexels -> Gemini fallback).
            is_podcast = (request.style or "").lower() == "podcast"
            if is_podcast:
                logger.info("Generating podcast cover...")
                self._generate_podcast_cover(script_path, settings.IMAGES_DIR)
            else:
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

            # Step 7b: Generate a thumbnail (poster) for the library
            self._generate_thumbnail(final_video_path)

            logger.info(f"Video generation complete: {video_filename}")

            # Step 8: Auto-publish to YouTube when the per-render flag is set OR
            # the global YOUTUBE_AUTO_UPLOAD setting is enabled.
            if request.publish_to_youtube or settings.YOUTUBE_AUTO_UPLOAD:
                self._publish_to_youtube(request, final_video_path)

        except Exception as e:
            logger.error(f"Video generation task failed: {str(e)}", exc_info=True)
            raise

    def _generate_podcast_cover(self, script_path: Path, images_dir: Path):
        """
        Podcast mode: source ONE cover image and hold it for every audio segment
        (so the existing assembler produces a single-cover episode with subtitles).
        """
        from imagegen.gen_img import get_image_for_prompt, save_image

        images_dir.mkdir(parents=True, exist_ok=True)
        with open(script_path, "r", encoding="utf-8") as f:
            script = json.load(f)

        segments = script.get("audio_script", []) or []
        count = max(1, len(segments))

        # Prefer a real cover prompt; fall back to the topic.
        visual = script.get("visual_script") or []
        cover_prompt = (visual[0].get("prompt") if visual else None) or script.get("topic", "")

        image_bytes = get_image_for_prompt(
            cover_prompt,
            pexels_api_key=settings.PEXELS_API_KEY,
            gemini_api_key=settings.GEMINI_API_KEY,
            aspect_ratio=settings.IMAGE_ASPECT_RATIO,
            gemini_model=settings.IMAGE_GEN_MODEL,
        )
        if not image_bytes:
            logger.warning("No cover image found for podcast; assembler will use a placeholder.")
            return

        # Save the cover once per segment so it stays on screen the whole episode.
        for idx in range(count):
            save_image(image_bytes, images_dir / f"scene_{idx:03d}.jpg")
        logger.info(f"Podcast cover applied across {count} segment(s).")

    def _generate_thumbnail(self, video_path: Path) -> Optional[Path]:
        """
        Extract a poster frame from the finished video (saved as <stem>.jpg next
        to it). Falls back to the first scene image. Best-effort: never raises.
        """
        thumb_path = video_path.with_suffix(".jpg")
        try:
            import imageio_ffmpeg
            ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
            # Grab a frame from the content (just after the ~5s intro).
            subprocess.run(
                [ffmpeg, "-y", "-ss", "6", "-i", str(video_path),
                 "-frames:v", "1", "-q:v", "3", str(thumb_path)],
                capture_output=True, timeout=60,
            )
            if thumb_path.exists() and thumb_path.stat().st_size > 0:
                logger.info(f"Thumbnail saved: {thumb_path.name}")
                return thumb_path
        except Exception as e:  # noqa: BLE001
            logger.warning(f"ffmpeg thumbnail failed ({e}); trying scene image fallback.")

        # Fallback: use the first generated scene image.
        try:
            images = sorted(settings.IMAGES_DIR.glob("*.jpg")) + sorted(settings.IMAGES_DIR.glob("*.png"))
            if images:
                shutil.copy(images[0], thumb_path)
                logger.info(f"Thumbnail (fallback) saved: {thumb_path.name}")
                return thumb_path
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Thumbnail fallback failed: {e}")
        return None

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
            # #Shorts in the title/description helps YouTube classify the
            # (vertical, <=60s) video as a Short.
            base_title = request.topic.strip()
            title = f"{base_title} #Shorts"[:100]
            description_parts = [f"{base_title}\n"]
            if request.key_points:
                description_parts.append("In this video:")
                description_parts.extend(f"- {point}" for point in request.key_points)
            description_parts.append("\n#Shorts #shorts #viral")
            description = "\n".join(description_parts)

            result = upload_video(
                file_path=video_path,
                title=title,
                description=description,
                tags=settings.youtube_tags_list + ["shorts", "viral"],
                privacy_status=request.privacy_status,
            )
            logger.info(f"Published to YouTube: {result['url']}")
        except YouTubeServiceError as e:
            logger.error(f"YouTube publishing failed: {e}")
        except Exception as e:  # noqa: BLE001
            logger.error(f"Unexpected error while publishing to YouTube: {e}", exc_info=True)
