"""
Meeting Assistant - Meetings Router
API endpoints for meeting management
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, HttpUrl
import logging

from ..core.supabase import get_db, get_user_from_token
from ..dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


# -------------------------------------------
# Pydantic Schemas
# -------------------------------------------

class MeetingCreate(BaseModel):
    """Schema for creating a meeting manually"""
    title: str
    meeting_url: HttpUrl
    meeting_provider: str = "google_meet"
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None


class MeetingUpdate(BaseModel):
    """Schema for updating a meeting"""
    title: Optional[str] = None
    should_record: Optional[bool] = None
    status: Optional[str] = None


class MeetingResponse(BaseModel):
    """Meeting response schema"""
    id: str
    title: str
    meeting_url: Optional[str]
    meeting_provider: str
    status: str
    scheduled_start: Optional[datetime]
    actual_start: Optional[datetime]
    actual_end: Optional[datetime]
    duration_seconds: Optional[int]
    created_at: datetime


# -------------------------------------------
# Endpoints
# -------------------------------------------

@router.get("/")
async def list_meetings(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: dict = Depends(get_current_user)
):
    """
    List all meetings for the current user
    
    - **status**: Filter by meeting status (scheduled, recording, completed, etc.)
    - **limit**: Number of results (max 100)
    - **offset**: Pagination offset
    """
    db = get_db(admin=True)
    meetings = db.get_user_meetings(
        user_id=user["id"],
        status=status,
        limit=limit,
        offset=offset
    )
    
    return {
        "meetings": meetings,
        "count": len(meetings),
        "limit": limit,
        "offset": offset
    }


@router.get("/upcoming")
async def get_upcoming_meetings(
    hours: int = Query(24, ge=1, le=168, description="Hours ahead to look"),
    user: dict = Depends(get_current_user)
):
    """
    Get upcoming scheduled meetings
    
    Returns meetings scheduled within the next N hours
    """
    db = get_db(admin=True)
    
    # Use the database function
    result = db.client.rpc(
        'get_upcoming_meetings',
        {
            'p_user_id': user["id"],
            'p_limit': 20
        }
    ).execute()
    
    return {
        "meetings": result.data or [],
        "hours_ahead": hours
    }


@router.post("/")
async def create_meeting(
    meeting: MeetingCreate,
    user: dict = Depends(get_current_user)
):
    """
    Create a new meeting manually
    
    Use this to add a meeting that wasn't detected from calendar
    """
    db = get_db(admin=True)
    
    new_meeting = db.create_meeting({
        "user_id": user["id"],
        "title": meeting.title,
        "meeting_url": str(meeting.meeting_url),
        "meeting_provider": meeting.meeting_provider,
        "status": "scheduled",
        "scheduled_start": meeting.scheduled_start.isoformat() if meeting.scheduled_start else None,
        "scheduled_end": meeting.scheduled_end.isoformat() if meeting.scheduled_end else None
    })
    
    logger.info(f"Created meeting {new_meeting['id']} for user {user['id']}")
    
    return new_meeting


@router.get("/{meeting_id}")
async def get_meeting(
    meeting_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Get a specific meeting with recordings and transcription
    """
    db = get_db(admin=True)
    meeting = db.get_meeting(meeting_id)
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if meeting["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return meeting


@router.patch("/{meeting_id}")
async def update_meeting(
    meeting_id: str,
    update: MeetingUpdate,
    user: dict = Depends(get_current_user)
):
    """
    Update a meeting
    """
    db = get_db(admin=True)
    
    # Verify ownership
    meeting = db.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if meeting["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update only provided fields
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    
    if not update_data:
        return meeting
    
    updated = db.update_meeting(meeting_id, update_data)
    
    logger.info(f"Updated meeting {meeting_id}")
    
    return updated


@router.delete("/{meeting_id}")
async def delete_meeting(
    meeting_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Delete a meeting and all associated recordings/transcriptions
    
    Note: This is a soft delete - recordings are kept in R2 but marked as deleted
    """
    db = get_db(admin=True)
    
    # Verify ownership
    meeting = db.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if meeting["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Soft delete by updating status
    db.update_meeting(meeting_id, {"status": "cancelled"})
    
    logger.info(f"Deleted meeting {meeting_id}")
    
    return {"message": "Meeting deleted", "meeting_id": meeting_id}


@router.post("/{meeting_id}/cancel")
async def cancel_meeting(
    meeting_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Cancel a scheduled meeting
    
    The bot will not join this meeting
    """
    db = get_db(admin=True)
    
    meeting = db.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if meeting["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if meeting["status"] not in ["scheduled", "joining", "waiting"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel meeting with status: {meeting['status']}"
        )
    
    db.update_meeting(meeting_id, {"status": "cancelled"})
    
    logger.info(f"Cancelled meeting {meeting_id}")
    
    return {"message": "Meeting cancelled", "meeting_id": meeting_id}


@router.post("/{meeting_id}/retry")
async def retry_meeting(
    meeting_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Retry a failed meeting
    
    Reschedules the bot to join the meeting
    """
    from ..core.redis import enqueue_job, Queues
    
    db = get_db(admin=True)
    
    meeting = db.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if meeting["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if meeting["status"] != "failed":
        raise HTTPException(
            status_code=400,
            detail="Can only retry failed meetings"
        )
    
    # Reset meeting status
    db.update_meeting(meeting_id, {
        "status": "scheduled",
        "error_message": None,
        "retry_count": meeting.get("retry_count", 0) + 1
    })
    
    # Enqueue join job
    job_id = await enqueue_job(Queues.JOIN_MEETING, {
        "meeting_id": meeting_id,
        "meeting_url": meeting["meeting_url"],
        "meeting_provider": meeting["meeting_provider"],
        "user_id": user["id"]
    })
    
    logger.info(f"Retrying meeting {meeting_id}, job {job_id}")
    
    return {
        "message": "Meeting retry scheduled",
        "meeting_id": meeting_id,
        "job_id": job_id
    }
