"""
Bring your own video.

A creator who already filmed and edited something still faces the busywork this
project exists to remove: write a title that does not bury the story, write a
description nobody reads but the algorithm does, think of twenty tags, make a
thumbnail, produce captions, upload, and do it again tomorrow. This module takes
the finished file and does all of it.

The one design rule: never re-encode
------------------------------------
Re-encoding a creator's video would cost minutes of CPU and a memory peak a
512 MB instance cannot survive, and it would degrade footage they already
graded. So every step here either reads the file or writes something small
beside it:

  probe        one ffprobe call, metadata only
  thumbnail    ONE frame extracted, composed to 1280x720 with Pillow
  audio        a 48 kbps mono track - roughly 3 MB for a ten minute video
  transcript   that audio to Gemini, which returns timed segments
  captions     an .srt written from those segments
  metadata     one more Gemini call for titles, description, tags, chapters
  publish      the ORIGINAL file uploaded byte for byte, then the thumbnail
               and the caption track attached to it afterwards

Subtitles are never burned in. YouTube renders the .srt sidecar itself, for
free, in whatever player the viewer is using - which is better than burning
them and costs a transcode instead of nothing.
"""
import json
import logging
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# Long enough for a real upload, short enough that a hung ffmpeg does not pin a
# worker forever. Extraction is I/O bound, so these are generous.
_PROBE_TIMEOUT = 60
_EXTRACT_TIMEOUT = 900

_THUMB_W, _THUMB_H = 1280, 720


class IngestError(RuntimeError):
    """Raised when a supplied video cannot be processed. Message is user-facing."""


@dataclass
class IngestJob:
    """Live state for one ingest, polled by the dashboard."""
    job_id: str
    filename: str
    stage: str = "queued"
    message: str = "Waiting to start"
    progress: int = 0
    error: Optional[str] = None
    result: Dict[str, Any] = field(default_factory=dict)
    started_at: float = field(default_factory=time.time)
    finished_at: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "filename": self.filename,
            "stage": self.stage,
            "message": self.message,
            "progress": self.progress,
            "error": self.error,
            "result": self.result,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "active": self.finished_at is None and self.error is None,
        }


# In-process, like the render status this app already keeps. One worker, one
# job at a time; a restart loses the job and the UI reports it stopped, which is
# the same tradeoff documented for renders.
_jobs: Dict[str, IngestJob] = {}
_JOB_HISTORY = 20


def get_job(job_id: str) -> Optional[IngestJob]:
    return _jobs.get(job_id)


def recent_jobs() -> List[Dict[str, Any]]:
    return [
        job.to_dict()
        for job in sorted(_jobs.values(), key=lambda j: j.started_at, reverse=True)
    ]


def _register(job: IngestJob) -> None:
    _jobs[job.job_id] = job
    if len(_jobs) > _JOB_HISTORY:
        oldest = sorted(_jobs.values(), key=lambda j: j.started_at)[: len(_jobs) - _JOB_HISTORY]
        for stale in oldest:
            _jobs.pop(stale.job_id, None)


# ------------------------------------------------------------------ ffmpeg ---

def _ffmpeg() -> str:
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def _run(args: List[str], timeout: int) -> subprocess.CompletedProcess:
    return subprocess.run(
        args, capture_output=True, timeout=timeout, check=False,
    )


def probe(video_path: Path) -> Dict[str, Any]:
    """Duration and dimensions, read from ffmpeg's own stderr banner.

    imageio-ffmpeg ships ffmpeg but not ffprobe, and pulling in a second binary
    to read a duration would be silly. `ffmpeg -i` with no output prints the
    same information and exits non-zero by design, so the return code is ignored
    on purpose.
    """
    result = _run([_ffmpeg(), "-hide_banner", "-i", str(video_path)], _PROBE_TIMEOUT)
    banner = (result.stderr or b"").decode("utf-8", errors="replace")

    info: Dict[str, Any] = {"duration": None, "width": None, "height": None,
                            "has_audio": False}

    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", banner)
    if match:
        hours, minutes, seconds = match.groups()
        info["duration"] = int(hours) * 3600 + int(minutes) * 60 + float(seconds)

    match = re.search(r"Video:.*?(\d{2,5})x(\d{2,5})", banner)
    if match:
        info["width"], info["height"] = int(match.group(1)), int(match.group(2))

    info["has_audio"] = "Audio:" in banner

    if info["duration"] is None:
        raise IngestError(
            "Could not read that file as a video. Supported: mp4, mov, mkv, webm, avi."
        )
    return info


# Where to sample candidate frames from, as a fraction of the running time.
# Nothing before 12% (intros, fades from black) or after 80% (outros, end cards).
_FRAME_SAMPLES = (0.15, 0.30, 0.45, 0.60, 0.75)


def pick_best_frame(video_path: Path, workdir: Path, duration: float) -> Optional[Path]:
    """Sample several frames and keep the sharpest.

    A single frame at a fixed offset is a coin toss: on a real edit, 25% in
    landed on a motion-blurred stock clip of a number plate, which then became
    the thumbnail. Sampling five points across the middle of the video and
    scoring each for edge detail reliably avoids the blurred and near-empty
    ones, because a frame with a subject in focus has far more edge energy than
    a smeared or flat one.

    Cheap: five keyframe seeks, and the scoring runs on a 320px copy.
    """
    candidates = []
    for index, fraction in enumerate(_FRAME_SAMPLES):
        at = duration * fraction
        if at < 0.5:
            continue
        path = workdir / f"cand{index}.jpg"
        if extract_frame(video_path, path, at):
            score = _sharpness(path)
            candidates.append((score, at, path))
            logger.debug("frame candidate %.1fs -> sharpness %.1f", at, score)

    if not candidates:
        # Fall back to the old fixed offset rather than giving up on a thumbnail.
        return extract_frame(video_path, workdir / "frame.jpg", max(1.0, duration * 0.25))

    candidates.sort(key=lambda c: c[0], reverse=True)
    best_score, best_at, best_path = candidates[0]
    logger.info("Thumbnail frame chosen at %.1fs (sharpness %.1f of %d candidates).",
                best_at, best_score, len(candidates))
    return best_path


def _sharpness(image_path: Path) -> float:
    """Edge energy as a focus proxy. Higher is sharper; 0.0 if unreadable."""
    try:
        from PIL import Image, ImageFilter, ImageStat

        with Image.open(image_path) as image:
            small = image.convert("L")
            small.thumbnail((320, 320))
            edges = small.filter(ImageFilter.FIND_EDGES)
            # Standard deviation of the edge map: a blurred or flat frame has
            # its edge energy spread thin, a focused one has strong outliers.
            return ImageStat.Stat(edges).stddev[0]
    except Exception as exc:  # noqa: BLE001
        logger.debug("Could not score %s: %s", image_path.name, exc)
        return 0.0


def extract_frame(video_path: Path, out_path: Path, at_seconds: float) -> Optional[Path]:
    """Pull a single frame. `-ss` before `-i` seeks by index rather than decoding
    up to the timestamp, which is the difference between instant and a minute."""
    result = _run([
        _ffmpeg(), "-y", "-ss", f"{max(0.0, at_seconds):.2f}", "-i", str(video_path),
        "-frames:v", "1", "-q:v", "3", str(out_path),
    ], _EXTRACT_TIMEOUT)
    if out_path.exists() and out_path.stat().st_size > 0:
        return out_path
    logger.warning("Frame extraction failed at %.1fs: %s", at_seconds,
                   (result.stderr or b"")[-400:].decode("utf-8", errors="replace"))
    return None


def extract_audio(video_path: Path, out_path: Path) -> Optional[Path]:
    """Mono, 16 kHz, 48 kbps AAC.

    Deliberately tiny. Speech recognition gains nothing from stereo or from
    music-grade bitrates, and this file has to be read into memory and posted to
    Gemini - a ten minute video lands around 3 MB instead of 100.
    """
    result = _run([
        _ffmpeg(), "-y", "-i", str(video_path), "-vn",
        "-ac", "1", "-ar", "16000", "-b:a", "48k", str(out_path),
    ], _EXTRACT_TIMEOUT)
    if out_path.exists() and out_path.stat().st_size > 0:
        return out_path
    logger.warning("Audio extraction failed: %s",
                   (result.stderr or b"")[-400:].decode("utf-8", errors="replace"))
    return None


# How far before the cut point to place the fast keyframe seek. Big enough to
# land before the preceding keyframe in normal footage, small enough that the
# accurate pass has almost nothing to discard.
_SEEK_LEAD_SECONDS = 3.0


def cut_clip(video_path: Path, out_path: Path, start: float, end: float) -> Optional[Path]:
    """Cut a segment by copying streams - no re-encode, so it costs almost nothing.

    Two seeks, deliberately. An input `-ss` alone is fast but lands on the
    nearest earlier keyframe and, with `-c copy`, does not discard what it
    skipped: asking for 5 seconds from 0:03 produced an 8 second file starting
    at zero. An output `-ss` alone is exact but reads the file from the
    beginning every time, which is slow on anything long.

    So: seek fast to a few seconds early, then trim the remainder exactly. Fast
    on a long video and accurate to the frame - a 5 second request now yields
    4.99 seconds instead of 8.01.
    """
    start = max(0.0, start)
    duration = max(1.0, end - start)
    lead = min(_SEEK_LEAD_SECONDS, start)

    result = _run([
        _ffmpeg(), "-y",
        "-ss", f"{start - lead:.2f}",   # fast, keyframe-aligned
        "-i", str(video_path),
        "-ss", f"{lead:.2f}",           # exact, on the decoded timeline
        "-t", f"{duration:.2f}",
        "-c", "copy", "-avoid_negative_ts", "make_zero",
        str(out_path),
    ], _EXTRACT_TIMEOUT)
    if out_path.exists() and out_path.stat().st_size > 0:
        return out_path
    logger.warning("Clip cut failed (%.1f-%.1f): %s", start, end,
                   (result.stderr or b"")[-300:].decode("utf-8", errors="replace"))
    return None


# --------------------------------------------------------------- thumbnail ---

def compose_thumbnail(frame_path: Path, out_path: Path, headline: str) -> Optional[Path]:
    """A frame, darkened at the bottom, with the headline set over it.

    Deliberately restrained: a legible line of type on the creator's own footage
    beats the usual generated collage, and it is the one thumbnail style that
    cannot look broken regardless of what the source frame contains.
    """
    try:
        from PIL import Image, ImageDraw, ImageFilter, ImageFont
    except Exception as exc:  # noqa: BLE001
        logger.warning("Pillow unavailable, skipping thumbnail: %s", exc)
        return None

    try:
        image = Image.open(frame_path).convert("RGB")

        # Cover-fit to 1280x720 rather than stretching: a squashed face reads as
        # broken far more than a cropped one.
        scale = max(_THUMB_W / image.width, _THUMB_H / image.height)
        resized = image.resize(
            (max(1, int(image.width * scale)), max(1, int(image.height * scale))),
            Image.LANCZOS,
        )
        left = (resized.width - _THUMB_W) // 2
        top = (resized.height - _THUMB_H) // 2
        canvas = resized.crop((left, top, left + _THUMB_W, top + _THUMB_H))

        # Gradient scrim. Built as a one-pixel-wide ramp and stretched, which is
        # both faster and smoother than drawing 300 rectangles.
        ramp = Image.new("L", (1, _THUMB_H))
        for y in range(_THUMB_H):
            fraction = y / _THUMB_H
            ramp.putpixel((0, y), int(235 * max(0.0, (fraction - 0.42) / 0.58) ** 1.4))
        scrim = Image.new("RGB", (_THUMB_W, _THUMB_H), (8, 8, 10))
        canvas = Image.composite(scrim, canvas, ramp.resize((_THUMB_W, _THUMB_H)))

        draw = ImageDraw.Draw(canvas)
        text = _thumbnail_text(headline)
        font = _load_font(64)
        lines = _wrap(text, font, draw, _THUMB_W - 120)[:3]

        line_height = 78
        block_height = line_height * len(lines)
        y = _THUMB_H - 70 - block_height
        for line in lines:
            # Cheap faux-shadow so the type survives a bright frame underneath.
            draw.text((62, y + 3), line, font=font, fill=(0, 0, 0))
            draw.text((60, y), line, font=font, fill=(255, 255, 255))
            y += line_height

        canvas.save(out_path, "JPEG", quality=88, optimize=True)
        return out_path
    except Exception as exc:  # noqa: BLE001
        logger.warning("Thumbnail composition failed: %s", exc)
        return None


def _thumbnail_text(headline: str) -> str:
    """Short, upper case, no trailing punctuation - thumbnail type, not a sentence."""
    text = re.sub(r"\s+", " ", headline or "").strip().rstrip(".!?,;:")
    words = text.split()
    if len(words) > 9:
        text = " ".join(words[:9])
    return text.upper()


def _load_font(size: int):
    from PIL import ImageFont
    # The repo ships a font for burned-in subtitles; reuse it so the thumbnail
    # matches the captions rather than falling back to a bitmap default.
    candidates = list((settings.RESOURCE_DIR / "font").glob("*.tt[fc]")) if settings.RESOURCE_DIR else []
    candidates += [Path("C:/Windows/Fonts/arialbd.ttf"),
                   Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")]
    for path in candidates:
        try:
            if path and Path(path).exists():
                return ImageFont.truetype(str(path), size)
        except Exception:  # noqa: BLE001
            continue
    return ImageFont.load_default()


def _wrap(text: str, font, draw, max_width: int) -> List[str]:
    words = text.split()
    lines: List[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=font) <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


# ------------------------------------------------------------------ Gemini ---

def _gemini_client():
    from google import genai
    keys = settings.gemini_api_keys_list if hasattr(settings, "gemini_api_keys_list") else []
    key = (keys[0] if keys else "") or settings.GEMINI_API_KEY
    if not key:
        raise IngestError(
            "Add a Gemini API key on the Connect screen - it writes the title, "
            "description, tags and captions."
        )
    return genai.Client(api_key=key)


def _gemini_json(client, contents, system: str) -> Dict[str, Any]:
    from google.genai import types

    response = client.models.generate_content(
        model=settings.GEMINI_TEXT_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system,
            temperature=0.4,
            max_output_tokens=8192,
            response_mime_type="application/json",
        ),
    )
    text = (response.text or "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Models occasionally wrap JSON in prose despite the mime type. Salvage
        # the outermost object rather than failing the whole ingest over it.
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise IngestError("The model did not return usable JSON.")


TRANSCRIBE_SYSTEM = (
    "You transcribe spoken audio into timed caption segments. Return every "
    "segment in order, 2 to 7 seconds each, with accurate start and end times "
    "in seconds. Transcribe what is actually said - never summarise, never "
    "invent dialogue, and never translate. If a stretch has no speech, omit it "
    "rather than inventing filler."
)


def transcribe(audio_path: Path, duration: float) -> List[Dict[str, Any]]:
    """Timed caption segments for the audio track.

    Never raises. Captions are valuable but not worth losing an upload over, so
    every failure here - including "there is no Gemini key" - returns an empty
    list and lets the rest of the pipeline continue. Building the client is
    inside the try for exactly that reason: it was outside once, and a missing
    key killed the whole job at this step with a message about metadata.
    """
    try:
        client = _gemini_client()
        from google.genai import types

        audio_bytes = audio_path.read_bytes()
        prompt = (
            f"Transcribe this {duration:.0f} second audio into caption segments.\n"
            'Return JSON: {"segments":[{"start":0.0,"end":3.2,"text":"..."}]}'
        )
        data = _gemini_json(
            client,
            [types.Part.from_bytes(data=audio_bytes, mime_type="audio/mp4"), prompt],
            TRANSCRIBE_SYSTEM,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Transcription failed, continuing without captions: %s", exc)
        return []

    segments = []
    for raw in data.get("segments", []):
        text = (raw.get("text") or "").strip()
        if not text:
            continue
        try:
            start = float(raw.get("start", 0))
            end = float(raw.get("end", start + 2))
        except (TypeError, ValueError):
            continue
        if end <= start:
            end = start + 2.0
        segments.append({"start": start, "end": end, "text": text})
    segments.sort(key=lambda s: s["start"])
    return segments


METADATA_SYSTEM = (
    "You are a YouTube packaging specialist. You write titles that state the "
    "specific thing the video delivers, descriptions that read like a person "
    "wrote them, and tags that a real viewer would type. You never use "
    "clickbait punctuation, ALL CAPS, or words like 'insane', 'shocking' and "
    "'you won't believe'."
)


def build_metadata(transcript_text: str, filename: str, duration: float,
                   profile: Dict[str, Any]) -> Dict[str, Any]:
    """Titles, description, tags, hashtags and chapters, in the channel's voice."""
    from app.services.profiles_service import script_directives

    client = _gemini_client()
    fmt = profile.get("format", {})
    hashtags = ", ".join(fmt.get("hashtags") or ["#shorts"])
    excerpt = transcript_text[:8000] if transcript_text else "(no speech detected)"

    prompt = f"""Package this video for YouTube.

{script_directives(profile)}

Source filename: {filename}
Duration: {duration:.0f} seconds
Channel hashtags to include: {hashtags}

Transcript:
{excerpt}

Return JSON with exactly these keys:
{{
  "titles": ["three title options, each under 70 characters, most specific first"],
  "description": "2-4 short paragraphs. First line repeats the hook, because that
                  is the only part shown before 'more'. End with the channel's
                  call to action, then the hashtags on their own line.",
  "tags": ["18-22 lowercase search terms a real viewer would type, no # prefix"],
  "hashtags": ["3-5 tags with the # prefix"],
  "chapters": [{{"time": "0:00", "label": "short chapter label"}}],
  "summary": "one sentence describing what the video actually covers"
}}

Rules:
- Titles must describe THIS video. A title that would fit any video is a failure.
- Only include chapters if the video is over 120 seconds and genuinely has
  sections. An empty list is the right answer for a short.
- Never invent facts that are not in the transcript."""

    data = _gemini_json(client, prompt, METADATA_SYSTEM)

    titles = [t.strip() for t in (data.get("titles") or []) if str(t).strip()][:3]
    if not titles:
        titles = [Path(filename).stem.replace("_", " ").replace("-", " ").title()[:100]]

    tags = [
        re.sub(r"^#", "", str(t)).strip().lower()
        for t in (data.get("tags") or []) if str(t).strip()
    ][:22]

    return {
        "titles": titles,
        "title": titles[0][:100],
        "description": (data.get("description") or "").strip()[:4900],
        "tags": tags,
        "hashtags": [str(h).strip() for h in (data.get("hashtags") or []) if str(h).strip()][:5],
        "chapters": data.get("chapters") or [],
        "summary": (data.get("summary") or "").strip(),
    }


def suggest_clips(segments: List[Dict[str, Any]], duration: float,
                  count: int = 3) -> List[Dict[str, Any]]:
    """Pick the moments worth cutting into Shorts.

    Only attempted for videos over two minutes: below that the whole video is
    already the clip, and asking a model to find the best 30 seconds of a
    90 second video wastes a call to be told "all of it".
    """
    if duration < 120 or not segments:
        return []
    client = _gemini_client()
    timeline = "\n".join(
        f'[{s["start"]:.0f}-{s["end"]:.0f}] {s["text"]}' for s in segments
    )[:12000]

    prompt = f"""Below is a timed transcript. Choose the {count} passages that
would work best as standalone vertical Shorts.

A good pick is self-contained - it makes sense to someone who has not seen the
rest - opens on something that earns the next three seconds, and lands a
complete point. Each must be 20 to 60 seconds.

Return JSON: {{"clips":[{{"start":0,"end":45,"title":"short punchy title",
"reason":"why this one works as a standalone clip"}}]}}

Transcript:
{timeline}"""

    try:
        data = _gemini_json(client, prompt, METADATA_SYSTEM)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Clip suggestion failed: %s", exc)
        return []

    clips = []
    for raw in (data.get("clips") or [])[:count]:
        try:
            start = max(0.0, float(raw.get("start", 0)))
            end = min(duration, float(raw.get("end", start + 30)))
        except (TypeError, ValueError):
            continue
        if end - start < 8:
            continue
        clips.append({
            "start": round(start, 2),
            "end": round(end, 2),
            "duration": round(end - start, 2),
            "title": (raw.get("title") or "Clip").strip()[:80],
            "reason": (raw.get("reason") or "").strip()[:240],
        })
    return clips


# --------------------------------------------------------------------- SRT ---

def write_srt(segments: List[Dict[str, Any]], out_path: Path) -> Optional[Path]:
    if not segments:
        return None
    lines = []
    for index, segment in enumerate(segments, start=1):
        lines.append(str(index))
        lines.append(f"{_srt_time(segment['start'])} --> {_srt_time(segment['end'])}")
        lines.append(segment["text"].strip())
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def _srt_time(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis >= 1000:  # rounding can tip .9996 over the second boundary
        millis, secs = 0, secs + 1
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


# ------------------------------------------------------------------ the job --

def process(job: IngestJob, source: Path, options: Dict[str, Any]) -> Dict[str, Any]:
    """Run one ingest end to end. Called on a background thread."""
    from app.services.profiles_service import store
    from app.services.storage_service import storage

    profile = store.active()
    workdir = Path(tempfile.mkdtemp(prefix="flux-ingest-"))
    stem = re.sub(r"[^a-zA-Z0-9_-]+", "-", Path(job.filename).stem)[:60] or "upload"

    def step(stage: str, message: str, progress: int) -> None:
        job.stage, job.message, job.progress = stage, message, progress
        logger.info("[ingest %s] %s - %s", job.job_id, stage, message)

    try:
        step("probe", "Reading the video", 5)
        info = probe(source)
        duration = info["duration"] or 0.0

        step("thumbnail", "Choosing a thumbnail frame", 15)
        frame = pick_best_frame(source, workdir, duration)

        segments: List[Dict[str, Any]] = []
        if info["has_audio"]:
            step("transcribe", "Transcribing the audio", 30)
            audio = extract_audio(source, workdir / "audio.m4a")
            if audio:
                segments = transcribe(audio, duration)
                # Free the audio immediately - on a 512 MB instance the video,
                # the audio and a Pillow canvas coexisting is the difference
                # between finishing and being OOM-killed.
                audio.unlink(missing_ok=True)
        else:
            logger.info("[ingest %s] no audio track; skipping captions", job.job_id)

        transcript_text = " ".join(s["text"] for s in segments)

        step("metadata", "Writing the title, description and tags", 55)
        metadata = build_metadata(transcript_text, job.filename, duration, profile)
        if options.get("title"):
            metadata["title"] = str(options["title"])[:100]

        srt = write_srt(segments, workdir / f"{stem}.srt")

        if frame:
            step("thumbnail", "Composing the thumbnail", 65)
            thumb = compose_thumbnail(frame, workdir / f"{stem}.jpg", metadata["title"])
        else:
            thumb = None

        clips: List[Dict[str, Any]] = []
        if options.get("suggest_clips", True):
            step("clips", "Looking for Shorts-worthy moments", 72)
            clips = suggest_clips(segments, duration)

        result: Dict[str, Any] = {
            "duration": round(duration, 2),
            "width": info["width"],
            "height": info["height"],
            "vertical": bool(info["width"] and info["height"] and info["height"] > info["width"]),
            "metadata": metadata,
            "captions": len(segments),
            "clips": clips,
            "published": None,
            "warnings": [],
        }

        if options.get("publish"):
            step("publish", "Uploading to YouTube", 80)
            result["published"] = _publish(
                source, srt, thumb, metadata, profile, options, result["warnings"]
            )
        else:
            result["warnings"].append(
                "Publishing was off for this run, so nothing was uploaded."
            )

        step("store", "Saving to your library", 92)
        if storage.available:
            try:
                storage.put_json(
                    {"kind": "ingest", "filename": job.filename, "created_at": time.time(),
                     "profile": profile.get("id"), **result},
                    f"{settings.B2_PREFIX.strip('/')}/ingest/{stem}-{job.job_id[:8]}.json",
                )
                if thumb:
                    storage.put_file(thumb, f"{settings.B2_PREFIX.strip('/')}/ingest/{stem}-{job.job_id[:8]}.jpg")
            except Exception as exc:  # noqa: BLE001
                logger.warning("Could not archive the ingest record: %s", exc)

        step("done", "Done", 100)
        job.result = result
        job.finished_at = time.time()
        return result

    except IngestError as exc:
        job.error = str(exc)
        job.stage, job.message, job.finished_at = "error", str(exc), time.time()
        raise
    except Exception as exc:  # noqa: BLE001
        logger.error("[ingest %s] failed: %s", job.job_id, exc, exc_info=True)
        job.error = f"Processing failed: {exc}"
        job.stage, job.message, job.finished_at = "error", job.error, time.time()
        raise
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
        # The upload itself is the largest thing on disk; on a 512 MB instance
        # with an ephemeral filesystem, leaving it behind fills the disk within
        # a handful of jobs.
        try:
            source.unlink(missing_ok=True)
        except Exception:  # noqa: BLE001
            pass


def _publish(source: Path, srt: Optional[Path], thumb: Optional[Path],
             metadata: Dict[str, Any], profile: Dict[str, Any],
             options: Dict[str, Any], warnings: List[str]) -> Optional[Dict[str, Any]]:
    from app.services import youtube_service

    description = metadata["description"]
    if metadata.get("hashtags"):
        tail = " ".join(metadata["hashtags"])
        if tail not in description:
            description = f"{description}\n\n{tail}"

    try:
        published = youtube_service.upload_video(
            file_path=source,
            title=metadata["title"],
            description=description,
            tags=metadata["tags"],
            privacy_status=options.get("privacy") or settings.YOUTUBE_PRIVACY_STATUS,
            category_id=profile.get("format", {}).get("youtube_category"),
        )
    except Exception as exc:  # noqa: BLE001
        # Everything produced so far is still worth keeping: the creator can
        # copy the title and description out and upload by hand.
        warnings.append(f"YouTube upload failed: {exc}")
        return None

    video_id = published.get("video_id")
    if thumb and video_id:
        if not youtube_service.set_thumbnail(video_id, thumb):
            warnings.append(
                "Custom thumbnail was rejected - YouTube requires a verified "
                "account for those. The video is live with an auto-generated frame."
            )
    if srt and video_id:
        if not youtube_service.upload_caption(video_id, srt):
            warnings.append("Caption upload failed; the video is live without captions.")

    return published
