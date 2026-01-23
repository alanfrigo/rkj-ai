"""
Meeting Assistant - Transcriptions Router
API endpoints for transcription management
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import Optional
import logging

from ..core.supabase import get_db
from ..services.transcription_service import get_transcription_service
from ..dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{transcription_id}")
async def get_transcription(
    transcription_id: str,
    include_segments: bool = Query(True, description="Include transcript segments"),
    user: dict = Depends(get_current_user)
):
    """
    Get a transcription by ID
    
    - **include_segments**: Whether to include segment-by-segment breakdown
    """
    db = get_db(admin=True)
    
    if include_segments:
        transcription = db.get_transcription(transcription_id)
    else:
        transcription = db.client.table('transcriptions')\
            .select('*')\
            .eq('id', transcription_id)\
            .single()\
            .execute().data
    
    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")
    
    # Verify ownership through meeting
    meeting = db.get_meeting(transcription["meeting_id"])
    if not meeting or meeting["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return transcription


@router.get("/meeting/{meeting_id}")
async def get_meeting_transcription(
    meeting_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Get transcription for a specific meeting
    """
    db = get_db(admin=True)
    
    # Verify meeting ownership
    meeting = db.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if meeting["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    transcription = db.get_meeting_transcription(meeting_id)
    
    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found for this meeting")
    
    return transcription


@router.get("/meeting/{meeting_id}/segments")
async def get_transcription_segments(
    meeting_id: str,
    start_time: Optional[int] = Query(None, description="Start time in ms"),
    end_time: Optional[int] = Query(None, description="End time in ms"),
    speaker_id: Optional[str] = Query(None, description="Filter by speaker"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user: dict = Depends(get_current_user)
):
    """
    Get transcription segments for a meeting
    
    Useful for:
    - Paginated loading of long transcriptions
    - Filtering by time range (for video sync)
    - Filtering by speaker
    """
    db = get_db(admin=True)
    
    # Verify meeting ownership
    meeting = db.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if meeting["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get transcription ID
    transcription = db.get_meeting_transcription(meeting_id)
    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")
    
    # Build query
    query = db.client.table('transcription_segments')\
        .select('*')\
        .eq('transcription_id', transcription['id'])\
        .order('segment_index')
    
    if start_time is not None:
        query = query.gte('start_time_ms', start_time)
    
    if end_time is not None:
        query = query.lte('end_time_ms', end_time)
    
    if speaker_id:
        query = query.eq('speaker_id', speaker_id)
    
    query = query.range(offset, offset + limit - 1)
    
    result = query.execute()
    
    return {
        "segments": result.data or [],
        "transcription_id": transcription['id'],
        "limit": limit,
        "offset": offset
    }


@router.post("/meeting/{meeting_id}/transcribe")
async def trigger_transcription(
    meeting_id: str,
    background_tasks: BackgroundTasks,
    language: str = Query("pt", description="Language code"),
    user: dict = Depends(get_current_user)
):
    """
    Manually trigger transcription for a meeting
    
    Use this to:
    - Retry a failed transcription
    - Transcribe a manually uploaded recording
    """
    db = get_db(admin=True)
    
    # Verify meeting ownership
    meeting = db.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if meeting["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if there's a recording
    recordings = meeting.get("recordings", [])
    audio_recording = next(
        (r for r in recordings if r["file_type"] in ["audio", "combined"]),
        None
    )
    
    if not audio_recording:
        raise HTTPException(
            status_code=400,
            detail="No audio recording found for this meeting"
        )
    
    # Check if already transcribing
    existing = db.get_meeting_transcription(meeting_id)
    if existing and existing["status"] == "processing":
        raise HTTPException(
            status_code=400,
            detail="Transcription already in progress"
        )
    
    # Enqueue transcription job
    from ..core.redis import enqueue_job, Queues
    
    job_id = await enqueue_job(Queues.TRANSCRIPTION, {
        "meeting_id": meeting_id,
        "recording_id": audio_recording["id"],
        "language": language,
        "user_id": user["id"]
    })
    
    # Update meeting status
    db.update_meeting(meeting_id, {"status": "transcribing"})
    
    logger.info(f"Triggered transcription for meeting {meeting_id}")
    
    return {
        "message": "Transcription started",
        "meeting_id": meeting_id,
        "job_id": job_id
    }


@router.get("/search")
async def search_transcriptions(
    query: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user)
):
    """
    Search across all transcriptions
    
    Full-text search through all meeting transcriptions
    """
    service = get_transcription_service()
    
    results = await service.search_transcriptions(
        user_id=user["id"],
        query=query,
        limit=limit
    )
    
    return {
        "query": query,
        "results": results,
        "count": len(results)
    }


@router.get("/{transcription_id}/export")
async def export_transcription(
    transcription_id: str,
    format: str = Query("txt", regex="^(txt|srt|vtt|json)$"),
    user: dict = Depends(get_current_user)
):
    """
    Export transcription in various formats
    
    Supported formats:
    - **txt**: Plain text
    - **srt**: SubRip subtitle format
    - **vtt**: WebVTT subtitle format
    - **json**: Full JSON with timestamps
    """
    db = get_db(admin=True)
    
    transcription = db.get_transcription(transcription_id)
    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")
    
    # Verify ownership
    meeting = db.get_meeting(transcription["meeting_id"])
    if not meeting or meeting["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    segments = transcription.get("transcription_segments", [])
    
    if format == "txt":
        content = transcription.get("full_text", "")
        content_type = "text/plain"
        filename = f"transcription_{transcription_id}.txt"
        
    elif format == "srt":
        content = _generate_srt(segments)
        content_type = "text/plain"
        filename = f"transcription_{transcription_id}.srt"
        
    elif format == "vtt":
        content = _generate_vtt(segments)
        content_type = "text/vtt"
        filename = f"transcription_{transcription_id}.vtt"
        
    else:  # json
        import json
        content = json.dumps({
            "transcription_id": transcription_id,
            "meeting_id": transcription["meeting_id"],
            "language": transcription["language"],
            "full_text": transcription.get("full_text"),
            "segments": segments
        }, indent=2, default=str)
        content_type = "application/json"
        filename = f"transcription_{transcription_id}.json"
    
    from fastapi.responses import Response
    
    return Response(
        content=content,
        media_type=content_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


def _generate_srt(segments: list) -> str:
    """Generate SRT subtitle format"""
    lines = []
    
    for i, segment in enumerate(segments, 1):
        start = _ms_to_srt_time(segment["start_time_ms"])
        end = _ms_to_srt_time(segment["end_time_ms"])
        text = segment["text"]
        
        lines.append(f"{i}")
        lines.append(f"{start} --> {end}")
        lines.append(text)
        lines.append("")
    
    return "\n".join(lines)


def _generate_vtt(segments: list) -> str:
    """Generate WebVTT subtitle format"""
    lines = ["WEBVTT", ""]
    
    for segment in segments:
        start = _ms_to_vtt_time(segment["start_time_ms"])
        end = _ms_to_vtt_time(segment["end_time_ms"])
        text = segment["text"]
        
        lines.append(f"{start} --> {end}")
        lines.append(text)
        lines.append("")
    
    return "\n".join(lines)


def _ms_to_srt_time(ms: int) -> str:
    """Convert milliseconds to SRT time format (HH:MM:SS,mmm)"""
    hours = ms // 3600000
    minutes = (ms % 3600000) // 60000
    seconds = (ms % 60000) // 1000
    milliseconds = ms % 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def _ms_to_vtt_time(ms: int) -> str:
    """Convert milliseconds to VTT time format (HH:MM:SS.mmm)"""
    hours = ms // 3600000
    minutes = (ms % 3600000) // 60000
    seconds = (ms % 60000) // 1000
    milliseconds = ms % 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
