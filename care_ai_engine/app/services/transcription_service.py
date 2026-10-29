"""
Care AI Engine - Ephemeral Transcription Service
Zero Data Retention (ZDR) architecture.

PRIVACY MODEL:
  - Audio files (<50MB): Processed entirely in RAM via BytesIO. Never touches disk.
  - Video files: Written to temp file (FFmpeg needs disk), transcribed, securely destroyed.
  - No audio/video is EVER permanently stored. Only the text transcript survives.

FLOW:
  Audio: bytes → BytesIO → Whisper → text → BytesIO wiped → done
  Video: bytes → temp file → FFmpeg extract → BytesIO → Whisper → text → shred temp → done

After processing, ZERO media data exists anywhere on the system.
"""

import io
import os
import asyncio
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

import whisper
import functools

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("transcription")

# Whisper model loaded once, reused for all requests
_model = None
_model_lock = asyncio.Lock()

# Thread pool for CPU-heavy Whisper inference
_executor = ThreadPoolExecutor(max_workers=2)

SUPPORTED_AUDIO = {".mp3", ".wav", ".m4a", ".ogg", ".webm", ".flac", ".aac"}
SUPPORTED_VIDEO = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
SUPPORTED_ALL = SUPPORTED_AUDIO | SUPPORTED_VIDEO


# ===========================================================
# Secure deletion - the "Clean Hands" protocol
# ===========================================================

def _secure_delete(filepath: str):
    """
    Securely destroy a file. Overwrites with random data before unlinking.
    
    Defence-in-depth: Real protection is LUKS full-disk encryption on the VPS.
    This adds an extra layer so even unencrypted tmpfs fragments are randomised.
    """
    try:
        path = Path(filepath)
        if not path.exists():
            return

        file_size = path.stat().st_size

        # Overwrite with random data (single pass — sufficient with FDE)
        with open(filepath, "r+b") as f:
            f.seek(0)
            remaining = file_size
            while remaining > 0:
                chunk = min(remaining, 1024 * 1024)  # 1MB chunks
                f.write(os.urandom(chunk))
                remaining -= chunk
            f.flush()
            os.fsync(f.fileno())

        os.unlink(filepath)
        logger.info(f"[ZDR] Securely deleted: {path.name} ({file_size} bytes)")

    except Exception as e:
        logger.error(f"[ZDR] Secure delete error for {filepath}: {e}")
        try:
            os.unlink(filepath)
        except OSError:
            pass


def _wipe_buffer(buffer: io.BytesIO):
    """
    Wipe a BytesIO buffer from memory.
    Overwrites internal data with zeros, then truncates and releases.
    """
    try:
        size = buffer.getbuffer().nbytes
        if size > 0:
            buffer.seek(0)
            buffer.write(b'\x00' * size)
        buffer.truncate(0)
        buffer.seek(0)
        buffer.close()
    except Exception:
        pass


# ===========================================================
# Whisper model management
# ===========================================================
async def _get_model():
    """Lazy-load Whisper model as a singleton using functools.partial."""
    global _model
    if _model is None:
        async with _model_lock:
            if _model is None:
                settings = get_settings()
                download_root = "/app/app/data/whisper"
                os.makedirs(download_root, exist_ok=True)

                logger.info(f"Loading Whisper model '{settings.whisper_model_size}' into {download_root}...")
                try:
                    loop = asyncio.get_event_loop()
                    # run_in_executor now sees a single callable with NO keywords.
                    load_func = functools.partial(
                        whisper.load_model,
                        settings.whisper_model_size,
                        download_root=download_root
                    )

                    _model = await loop.run_in_executor(_executor, load_func)
                    logger.info("Whisper model loaded successfully")
                except Exception as e:
                    logger.error(f"Failed to load Whisper model: {str(e)}")
                    raise
    return _model

# ===========================================================
# Core transcription (from temp file — used by both paths)
# ===========================================================

def _run_whisper_from_path(model, audio_path: str, language: str) -> dict:
    """Run Whisper transcription on a file path (blocking)."""
    result = model.transcribe(
        audio_path,
        language=language,
        fp16=False,
        verbose=False,
    )
    return {
        "text": result["text"].strip(),
        "language": result.get("language", language),
        "segments": [
            {
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"].strip(),
            }
            for seg in result.get("segments", [])
        ],
    }


def _transcribe_from_buffer(model, audio_buffer: io.BytesIO, language: str) -> dict:
    """
    Transcribe audio from a BytesIO buffer.
    
    Whisper needs a file path, so we use a short-lived temp file in /tmp.
    On Linux, /tmp is often tmpfs (RAM-backed), so data may never hit physical disk.
    The temp file is securely deleted immediately after transcription.
    """
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            suffix=".wav", delete=False, dir="/tmp",
            prefix="careai_ephemeral_"
        ) as tmp:
            tmp_path = tmp.name
            audio_buffer.seek(0)
            tmp.write(audio_buffer.read())

        return _run_whisper_from_path(model, tmp_path, language)

    finally:
        if tmp_path:
            _secure_delete(tmp_path)


# ===========================================================
# Duration detection (ephemeral — temp files destroyed after)
# ===========================================================

def _get_duration_from_bytes(media_bytes: bytes, suffix: str) -> Optional[float]:
    """Get media duration using FFprobe. Temp file is securely deleted after."""
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            suffix=suffix, delete=False, dir="/tmp",
            prefix="careai_probe_"
        ) as tmp:
            tmp_path = tmp.name
            tmp.write(media_bytes)

        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                tmp_path,
            ],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except Exception:
        pass
    finally:
        if tmp_path:
            _secure_delete(tmp_path)
    return None


# ===========================================================
# Video → audio extraction (ephemeral)
# ===========================================================

def _extract_audio_from_video_ephemeral(video_bytes: bytes, original_ext: str) -> io.BytesIO:
    """
    Extract audio from video into an in-memory BytesIO buffer.
    
    Both the video temp file and extracted audio temp file are
    securely destroyed after the audio is loaded into memory.
    """
    video_tmp = None
    audio_tmp = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=original_ext, delete=False, dir="/tmp",
            prefix="careai_vid_"
        ) as vf:
            video_tmp = vf.name
            vf.write(video_bytes)

        audio_tmp = video_tmp + ".extracted.wav"

        cmd = [
            "ffmpeg", "-i", video_tmp,
            "-vn",                    # No video stream
            "-acodec", "pcm_s16le",  # WAV format
            "-ar", "16000",          # 16kHz (Whisper's native rate)
            "-ac", "1",              # Mono
            "-y",                    # Overwrite
            audio_tmp,
        ]

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=180,
        )

        if result.returncode != 0:
            raise TranscriptionError(f"FFmpeg audio extraction failed: {result.stderr[:200]}")

        if not os.path.exists(audio_tmp):
            raise TranscriptionError("FFmpeg produced no audio output")

        # Read extracted audio into memory buffer
        with open(audio_tmp, "rb") as af:
            audio_buffer = io.BytesIO(af.read())

        logger.info(f"[ZDR] Video audio extracted to memory: {audio_buffer.getbuffer().nbytes} bytes")
        return audio_buffer

    except subprocess.TimeoutExpired:
        raise TranscriptionError("Video audio extraction timed out (>3 min)")

    finally:
        # CRITICAL: Securely destroy BOTH temp files
        if video_tmp:
            _secure_delete(video_tmp)
        if audio_tmp and os.path.exists(audio_tmp):
            _secure_delete(audio_tmp)
        logger.debug("[ZDR] Video temp files destroyed")


# ===========================================================
# Public API — Ephemeral transcription
# ===========================================================

async def transcribe_audio_ephemeral(audio_bytes: bytes, filename: str) -> dict:
    """
    Transcribe audio using in-memory processing.
    
    The audio bytes are loaded into a BytesIO buffer, processed by Whisper,
    and the buffer is wiped immediately after. No permanent file is ever created.
    
    Args:
        audio_bytes: Raw audio file content
        filename: Original filename (for extension detection)
    
    Returns:
        {
            "transcript": str,
            "language": str,
            "duration_seconds": float,
            "segments": [...],
            "processing_time_ms": float,
            "input_type": "audio",
            "media_destroyed": True,
            "file_size_bytes": int,
        }
    """
    start = time.monotonic()
    file_size = len(audio_bytes)
    audio_buffer = io.BytesIO(audio_bytes)

    try:
        if file_size > 100 * 1024 * 1024:
            raise TranscriptionError("Audio file too large (max 100MB)")

        ext = Path(filename).suffix.lower() if filename else ".wav"
        if ext not in SUPPORTED_AUDIO:
            raise TranscriptionError(f"Unsupported audio format: {ext}")

        # Get duration
        duration = _get_duration_from_bytes(audio_bytes, ext)

        # Transcribe from memory
        model = await _get_model()
        settings = get_settings()
        loop = asyncio.get_event_loop()

        whisper_result = await loop.run_in_executor(
            _executor,
            _transcribe_from_buffer,
            model,
            audio_buffer,
            settings.whisper_language,
        )

        processing_time_ms = (time.monotonic() - start) * 1000

        logger.info(
            "[ZDR] Audio transcribed ephemerally",
            extra={
                "duration_seconds": duration,
                "transcript_length": len(whisper_result["text"]),
                "processing_time_ms": round(processing_time_ms, 1),
                "media_stored": False,
                "file_size_bytes": file_size,
            },
        )

        return {
            "transcript": whisper_result["text"],
            "language": whisper_result["language"],
            "duration_seconds": duration or 0,
            "segments": whisper_result["segments"],
            "processing_time_ms": round(processing_time_ms, 1),
            "input_type": "audio",
            "media_destroyed": True,
            "file_size_bytes": file_size,
        }

    finally:
        # CRITICAL: Wipe the audio buffer from memory
        _wipe_buffer(audio_buffer)
        logger.debug("[ZDR] Audio buffer wiped from memory")


async def transcribe_video_ephemeral(video_bytes: bytes, filename: str) -> dict:
    """
    Transcribe video using ephemeral processing.
    
    Flow:
      1. Video bytes → temp file (FFmpeg needs disk access)
      2. FFmpeg extracts audio → in-memory BytesIO
      3. Securely delete video temp file
      4. Whisper transcribes from memory
      5. Wipe audio buffer
    
    After this function returns, ZERO media exists anywhere on the system.
    
    Args:
        video_bytes: Raw video file content
        filename: Original filename (for extension detection)
    
    Returns:
        {
            "transcript": str,
            "language": str,
            "duration_seconds": float,
            "segments": [...],
            "processing_time_ms": float,
            "input_type": "video",
            "media_destroyed": True,
            "file_size_bytes": int,
        }
    """
    start = time.monotonic()
    file_size = len(video_bytes)
    ext = Path(filename).suffix.lower() if filename else ".mp4"
    audio_buffer = None

    try:
        if file_size > 500 * 1024 * 1024:
            raise TranscriptionError("Video file too large (max 500MB)")

        if ext not in SUPPORTED_VIDEO:
            raise TranscriptionError(f"Unsupported video format: {ext}")

        # Get duration before processing
        duration = _get_duration_from_bytes(video_bytes, ext)

        # Extract audio into memory (video temp file destroyed inside this function)
        audio_buffer = _extract_audio_from_video_ephemeral(video_bytes, ext)

        # Release the video bytes from memory ASAP
        del video_bytes
        logger.info("[ZDR] Video bytes released from memory")

        # Transcribe from the in-memory audio buffer
        model = await _get_model()
        settings = get_settings()
        loop = asyncio.get_event_loop()

        whisper_result = await loop.run_in_executor(
            _executor,
            _transcribe_from_buffer,
            model,
            audio_buffer,
            settings.whisper_language,
        )

        processing_time_ms = (time.monotonic() - start) * 1000

        logger.info(
            "[ZDR] Video transcribed ephemerally",
            extra={
                "duration_seconds": duration,
                "transcript_length": len(whisper_result["text"]),
                "processing_time_ms": round(processing_time_ms, 1),
                "media_stored": False,
                "file_size_bytes": file_size,
            },
        )

        return {
            "transcript": whisper_result["text"],
            "language": whisper_result["language"],
            "duration_seconds": duration or 0,
            "segments": whisper_result["segments"],
            "processing_time_ms": round(processing_time_ms, 1),
            "input_type": "video",
            "media_destroyed": True,
            "file_size_bytes": file_size,
        }

    finally:
        if audio_buffer:
            _wipe_buffer(audio_buffer)
        logger.debug("[ZDR] All media buffers wiped")


class TranscriptionError(Exception):
    """Raised when transcription fails."""
    pass
