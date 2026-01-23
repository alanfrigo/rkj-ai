"""
Meeting Assistant - Recordings Router
API endpoints for recording management
"""
from fastapi import APIRouter, Depends, HTTPException, Query
import logging

from ..core.supabase import get_db
from ..core.r2 import get_r2_storage
from ..dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{recording_id}")
async def get_recording(
    recording_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Get recording details
    """
    db = get_db(admin=True)
    
    recording = db.get_recording(recording_id)
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    # Verify ownership through meeting
    meeting = db.get_meeting(recording["meeting_id"])
    if not meeting or meeting["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return recording


@router.get("/{recording_id}/url")
async def get_recording_url(
    recording_id: str,
    expiration: int = Query(3600, ge=300, le=86400, description="URL expiration in seconds"),
    user: dict = Depends(get_current_user)
):
    """
    Get a presigned URL to download/stream the recording
    
    - **expiration**: How long the URL is valid (5 min to 24 hours)
    """
    db = get_db(admin=True)
    r2 = get_r2_storage()
    
    recording = db.get_recording(recording_id)
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    # Verify ownership
    meeting = db.get_meeting(recording["meeting_id"])
    if not meeting or meeting["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Generate presigned URL
    url = r2.get_presigned_url(
        storage_path=recording["storage_path"],
        expiration=expiration
    )
    
    return {
        "url": url,
        "expires_in": expiration,
        "recording_id": recording_id,
        "file_type": recording["file_type"],
        "format": recording.get("format")
    }


@router.get("/meeting/{meeting_id}")
async def get_meeting_recordings(
    meeting_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Get all recordings for a meeting
    """
    db = get_db(admin=True)
    
    # Verify ownership
    meeting = db.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if meeting["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    result = db.client.table('recordings')\
        .select('*')\
        .eq('meeting_id', meeting_id)\
        .order('created_at')\
        .execute()
    
    return {
        "recordings": result.data or [],
        "meeting_id": meeting_id
    }


@router.delete("/{recording_id}")
async def delete_recording(
    recording_id: str,
    delete_from_storage: bool = Query(False, description="Also delete from R2"),
    user: dict = Depends(get_current_user)
):
    """
    Delete a recording
    
    - **delete_from_storage**: If true, also deletes the file from R2
    """
    db = get_db(admin=True)
    r2 = get_r2_storage()
    
    recording = db.get_recording(recording_id)
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    # Verify ownership
    meeting = db.get_meeting(recording["meeting_id"])
    if not meeting or meeting["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Delete from storage if requested
    if delete_from_storage and recording.get("storage_path"):
        try:
            r2.delete_file(recording["storage_path"])
            logger.info(f"Deleted file from R2: {recording['storage_path']}")
        except Exception as e:
            logger.error(f"Failed to delete from R2: {e}")
    
    # Delete from database
    db.client.table('recordings')\
        .delete()\
        .eq('id', recording_id)\
        .execute()
    
    logger.info(f"Deleted recording {recording_id}")
    
    return {
        "message": "Recording deleted",
        "recording_id": recording_id,
        "storage_deleted": delete_from_storage
    }


@router.get("/{recording_id}/thumbnail")
async def get_thumbnail_url(
    recording_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Get thumbnail URL for a video recording
    """
    db = get_db(admin=True)
    r2 = get_r2_storage()
    
    recording = db.get_recording(recording_id)
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    # Verify ownership
    meeting = db.get_meeting(recording["meeting_id"])
    if not meeting or meeting["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not recording.get("thumbnail_path"):
        raise HTTPException(status_code=404, detail="Thumbnail not available")
    
    url = r2.get_presigned_url(
        storage_path=recording["thumbnail_path"],
        expiration=3600
    )
    
    return {
        "url": url,
        "recording_id": recording_id
    }
