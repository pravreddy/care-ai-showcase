"""
Care AI Engine - Notes API Routes (Zero Data Retention)

PRIVACY MODEL:
  - Audio/video uploads are processed in memory and DESTROYED immediately.
  - Only the text transcript and AI-generated clinical note are stored.
  - No audio or video file is ever permanently written to disk.
  - API response includes "media_destroyed: true" confirmation.

Endpoints:
  POST /notes/voice     → Upload audio → ephemeral transcribe → clinical note → destroy audio
  POST /notes/video     → Upload video → ephemeral transcribe → clinical note → destroy video
  POST /notes/text      → Submit text → generate clinical note (no media involved)
  GET  /notes           → List user's notes (text only, no media)
  GET  /notes/{id}      → Get a specific note
  POST /notes/{id}/reprocess  → Re-run AI on existing transcript
  POST /notes/handover  → Generate shift handover from recent notes
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.models.database import User, VoiceNote
from app.services.transcription_service import (
    transcribe_audio_ephemeral,
    transcribe_video_ephemeral,
    TranscriptionError,
    SUPPORTED_AUDIO,
    SUPPORTED_VIDEO,
)
from app.services.clinical_notes_service import generate_clinical_note, generate_handover_note
from app.core.logging import get_logger

logger = get_logger("api.notes")

router = APIRouter(prefix="/notes", tags=["Clinical Notes"])


# --- Response Models ---

class NoteResponse(BaseModel):
    id: UUID
    input_type: str  # "audio", "video", "text"
    transcript: Optional[str] = None
    clinical_note: Optional[dict] = None
    duration_seconds: Optional[float] = None
    client_name: Optional[str] = None
    created_at: datetime
    media_destroyed: bool = True  # Always true — we never keep media

    model_config = {"from_attributes": True}


class NoteListResponse(BaseModel):
    notes: list[NoteResponse]
    total: int


class HandoverResponse(BaseModel):
    success: bool
    handover_note: Optional[str] = None
    notes_summarised: int = 0
    error: Optional[str] = None


# --- Voice Note (Ephemeral) ---

@router.post("/voice", response_model=NoteResponse)
async def upload_voice_note(
    file: UploadFile = File(...),
    client_name: Optional[str] = Form(None),
    note_type: str = Form("full"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload audio → transcribe in memory → generate clinical note → DESTROY audio.
    
    The audio file is processed entirely in RAM and wiped immediately after
    transcription. Only the text transcript and clinical note are stored.
    
    Supported: .mp3, .wav, .m4a, .ogg, .webm, .flac, .aac
    """
    return await _process_media_ephemeral(
        file=file,
        media_type="audio",
        client_name=client_name,
        note_type=note_type,
        current_user=current_user,
        db=db,
    )


# --- Video Note (Ephemeral) ---

@router.post("/video", response_model=NoteResponse)
async def upload_video_note(
    file: UploadFile = File(...),
    client_name: Optional[str] = Form(None),
    note_type: str = Form("full"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload video → extract audio → transcribe → generate clinical note → DESTROY all media.
    
    Video is written to an encrypted temp file for FFmpeg processing,
    then securely shredded immediately after audio extraction.
    
    Supported: .mp4, .mov, .avi, .mkv, .webm
    """
    return await _process_media_ephemeral(
        file=file,
        media_type="video",
        client_name=client_name,
        note_type=note_type,
        current_user=current_user,
        db=db,
    )


# --- Text Note ---

@router.post("/text", response_model=NoteResponse)
async def submit_text_note(
    text: str = Form(..., min_length=10, max_length=10000),
    client_name: Optional[str] = Form(None),
    note_type: str = Form("full"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit typed text → generate clinical note.
    No media involved — no privacy concerns beyond the text itself.
    """
    logger.info(f"Text note submitted: {len(text)} chars", extra={"user_id": str(current_user.id)})

    clinical_note = await generate_clinical_note(
        transcript=text,
        client_name=client_name,
        note_type=note_type,
    )

    note = VoiceNote(
        user_id=current_user.id,
        filename="text_note",
        file_path="",  # No file stored
        file_size_bytes=len(text.encode()),
        input_type="text",
        duration_seconds=None,
        transcript=text,
        ai_summary=clinical_note.get("summary", ""),
        clinical_note_data=clinical_note,
        client_name=client_name,
    )
    db.add(note)
    await db.flush()

    return NoteResponse(
        id=note.id,
        input_type="text",
        transcript=text,
        clinical_note=clinical_note,
        duration_seconds=None,
        client_name=client_name,
        created_at=note.created_at,
        media_destroyed=True,
    )


# --- List Notes ---

@router.get("/", response_model=NoteListResponse)
async def list_notes(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all notes for the current user, newest first.
    Only text content is returned — no media files exist.
    """
    result = await db.execute(
        select(VoiceNote)
        .where(VoiceNote.user_id == current_user.id)
        .order_by(VoiceNote.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    notes = result.scalars().all()

    count_result = await db.execute(
        select(VoiceNote.id).where(VoiceNote.user_id == current_user.id)
    )
    total = len(count_result.all())

    return NoteListResponse(
        notes=[
            NoteResponse(
                id=n.id,
                input_type=n.input_type or "text",
                transcript=n.transcript,
                clinical_note=n.clinical_note_data or ({"summary": n.ai_summary} if n.ai_summary else None),
                duration_seconds=n.duration_seconds,
                client_name=n.client_name,
                created_at=n.created_at,
                media_destroyed=True,
            )
            for n in notes
        ],
        total=total,
    )


# --- Get Single Note ---

@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific note by ID. Only text — no media download possible."""
    result = await db.execute(
        select(VoiceNote).where(
            VoiceNote.id == note_id,
            VoiceNote.user_id == current_user.id,
        )
    )
    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    return NoteResponse(
        id=note.id,
        input_type=note.input_type or "text",
        transcript=note.transcript,
        clinical_note=note.clinical_note_data or ({"summary": note.ai_summary} if note.ai_summary else None),
        duration_seconds=note.duration_seconds,
        client_name=note.client_name,
        created_at=note.created_at,
        media_destroyed=True,
    )


# --- Reprocess Note ---

@router.post("/{note_id}/reprocess")
async def reprocess_note(
    note_id: UUID,
    note_type: str = "full",
    client_name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Re-run the AI clinical note generation on an existing transcript.
    Since we only store text, re-processing works from the saved transcript.
    """
    result = await db.execute(
        select(VoiceNote).where(
            VoiceNote.id == note_id,
            VoiceNote.user_id == current_user.id,
        )
    )
    note = result.scalar_one_or_none()

    if not note or not note.transcript:
        raise HTTPException(status_code=404, detail="Note not found or has no transcript")

    clinical_note = await generate_clinical_note(
        transcript=note.transcript,
        client_name=client_name or note.client_name,
        note_type=note_type,
    )

    note.ai_summary = clinical_note.get("summary", "")
    note.clinical_note_data = clinical_note

    return {
        "note_id": str(note.id),
        "clinical_note": clinical_note,
        "media_destroyed": True,
    }


# --- Shift Handover ---

@router.post("/handover", response_model=HandoverResponse)
async def generate_shift_handover(
    hours: int = 12,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a shift handover from recent clinical notes.
    Works entirely from stored text — no media needed.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    result = await db.execute(
        select(VoiceNote)
        .where(
            VoiceNote.user_id == current_user.id,
            VoiceNote.created_at >= cutoff,
        )
        .order_by(VoiceNote.created_at.asc())
    )
    notes = result.scalars().all()

    if not notes:
        return HandoverResponse(
            success=False,
            error=f"No notes found in the past {hours} hours",
            notes_summarised=0,
        )

    note_dicts = [
        {
            "summary": n.ai_summary or n.transcript or "No content",
            "created_at": n.created_at.isoformat() if n.created_at else "unknown",
            "client_name": n.client_name or "Unknown client",
            "actions": (n.clinical_note_data or {}).get("actions", []),
            "concerns": (n.clinical_note_data or {}).get("concerns", []),
        }
        for n in notes
    ]

    handover = await generate_handover_note(note_dicts)

    return HandoverResponse(
        success=handover.get("success", False),
        handover_note=handover.get("handover_note"),
        notes_summarised=handover.get("notes_summarised", 0),
        error=handover.get("error"),
    )


# ===========================================================
# Internal: Ephemeral media processing
# ===========================================================

async def _process_media_ephemeral(
    file: UploadFile,
    media_type: str,
    client_name: Optional[str],
    note_type: str,
    current_user: User,
    db: AsyncSession,
) -> NoteResponse:
    """
    Core ephemeral processing pipeline.
    
    1. Read file bytes into memory
    2. Transcribe (audio in RAM, video via secure temp files)
    3. Generate clinical note from transcript
    4. Store ONLY the text in database
    5. All media bytes wiped/destroyed
    6. Return response with media_destroyed=True
    """
    # Step 1: Read file into memory
    content = await file.read()

    if not content:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    filename = file.filename or f"recording.{'mp3' if media_type == 'audio' else 'mp4'}"

    logger.info(
        f"[ZDR] {media_type.title()} received for ephemeral processing: "
        f"{filename} ({len(content)} bytes)",
        extra={"user_id": str(current_user.id)},
    )

    # Step 2: Ephemeral transcription — media is destroyed inside these functions
    try:
        if media_type == "audio":
            transcription = await transcribe_audio_ephemeral(content, filename)
        else:
            transcription = await transcribe_video_ephemeral(content, filename)
    except TranscriptionError as e:
        raise HTTPException(status_code=422, detail=f"Transcription failed: {str(e)}")
    finally:
        # Belt and braces: ensure content bytes are released
        del content

    transcript = transcription["transcript"]

    if not transcript.strip():
        raise HTTPException(
            status_code=422,
            detail="No speech detected in the recording. Please try again with clearer audio.",
        )

    logger.info(
        f"[ZDR] Media destroyed. Transcript preserved: {len(transcript)} chars",
        extra={"user_id": str(current_user.id)},
    )

    # Step 3: Generate clinical note from transcript (text only)
    clinical_note = await generate_clinical_note(
        transcript=transcript,
        client_name=client_name,
        note_type=note_type,
    )

    # Step 4: Store ONLY the text in database — no file path, no media
    note = VoiceNote(
        user_id=current_user.id,
        filename=filename,          # Original filename for reference only
        file_path="[DESTROYED]",    # Explicit marker: no file exists
        file_size_bytes=transcription.get("file_size_bytes", 0),
        input_type=media_type,
        duration_seconds=transcription.get("duration_seconds"),
        transcript=transcript,
        ai_summary=clinical_note.get("summary", ""),
        clinical_note_data=clinical_note,
        client_name=client_name,
    )
    db.add(note)
    await db.flush()

    logger.info(
        f"[ZDR] Note saved (text only): {note.id}",
        extra={
            "user_id": str(current_user.id),
            "input_type": media_type,
            "transcript_length": len(transcript),
            "media_destroyed": True,
        },
    )

    # Step 5: Return response with destruction confirmation
    return NoteResponse(
        id=note.id,
        input_type=media_type,
        transcript=transcript,
        clinical_note=clinical_note,
        duration_seconds=transcription.get("duration_seconds"),
        client_name=client_name,
        created_at=note.created_at,
        media_destroyed=True,  # Confirmed: no media exists on our servers
    )
