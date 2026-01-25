"""
Meeting Assistant - Calendar Router
API endpoints for calendar management and sync
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
import logging

from ..core.supabase import get_db
from ..dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/connected")
async def list_connected_calendars(
    user: dict = Depends(get_current_user)
):
    """
    List all connected calendars for the current user
    """
    db = get_db(admin=True)
    
    result = db.client.table('connected_calendars')\
        .select('*')\
        .eq('user_id', user["id"])\
        .order('created_at', desc=True)\
        .execute()
    
    return {
        "calendars": result.data or []
    }


@router.get("/events")
async def list_calendar_events(
    hours: int = Query(24, ge=1, le=168, description="Hours ahead to look"),
    include_past: bool = Query(False, description="Include past events"),
    user: dict = Depends(get_current_user)
):
    """
    List calendar events
    
    - **hours**: How many hours ahead to look (max 7 days)
    - **include_past**: Include events from the past 24 hours
    """
    from datetime import datetime, timedelta
    
    db = get_db(admin=True)
    
    now = datetime.utcnow()
    end_time = now + timedelta(hours=hours)
    
    query = db.client.table('calendar_events')\
        .select('*')\
        .eq('user_id', user["id"])\
        .eq('is_excluded', False)\
        .lte('start_time', end_time.isoformat())\
        .order('start_time')
    
    if include_past:
        start_time = now - timedelta(hours=24)
        query = query.gte('start_time', start_time.isoformat())
    else:
        query = query.gte('start_time', now.isoformat())
    
    result = query.execute()
    
    return {
        "events": result.data or [],
        "hours_ahead": hours
    }


@router.post("/sync")
async def trigger_calendar_sync(
    calendar_id: Optional[str] = Query(None, description="Specific calendar to sync"),
    user: dict = Depends(get_current_user)
):
    """
    Manually trigger calendar sync
    
    Syncs events from Google Calendar
    """
    from ..core.redis import enqueue_job, Queues
    
    job_id = await enqueue_job(Queues.CALENDAR_SYNC, {
        "user_id": user["id"],
        "calendar_id": calendar_id
    })
    
    logger.info(f"Triggered calendar sync for user {user['id']}")
    
    return {
        "message": "Calendar sync started",
        "job_id": job_id
    }


@router.patch("/events/{event_id}")
async def update_event_settings(
    event_id: str,
    should_record: bool = Query(..., description="Whether to record this event"),
    user: dict = Depends(get_current_user)
):
    """
    Update recording settings for a calendar event
    """
    db = get_db(admin=True)
    
    # Verify ownership
    event = db.client.table('calendar_events')\
        .select('*')\
        .eq('id', event_id)\
        .single()\
        .execute().data
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    if event["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update
    result = db.client.table('calendar_events')\
        .update({"should_record": should_record})\
        .eq('id', event_id)\
        .execute()
    
    return result.data[0] if result.data else event


@router.patch("/events/{event_id}/exclude")
async def exclude_event(
    event_id: str,
    exclude: bool = Query(True, description="Whether to exclude this event"),
    user: dict = Depends(get_current_user)
):
    """
    Exclude an event from the system (soft delete)
    
    This marks the event as excluded without deleting it from the user's real calendar.
    Excluded events won't appear in listings or be considered for recording.
    """
    db = get_db(admin=True)
    
    # Verify ownership
    event = db.client.table('calendar_events')\
        .select('*')\
        .eq('id', event_id)\
        .single()\
        .execute().data
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    if event["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update is_excluded status
    result = db.client.table('calendar_events')\
        .update({"is_excluded": exclude})\
        .eq('id', event_id)\
        .execute()
    
    logger.info(f"Event {event_id} {'excluded' if exclude else 'restored'} by user {user['id']}")
    
    return result.data[0] if result.data else event


@router.delete("/connected/{calendar_id}")
async def disconnect_calendar(
    calendar_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Disconnect a calendar
    """
    db = get_db(admin=True)
    
    # Verify ownership
    calendar = db.client.table('connected_calendars')\
        .select('*')\
        .eq('id', calendar_id)\
        .single()\
        .execute().data
    
    if not calendar:
        raise HTTPException(status_code=404, detail="Calendar not found")
    
    if calendar["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Soft delete - mark as inactive
    db.client.table('connected_calendars')\
        .update({"is_active": False})\
        .eq('id', calendar_id)\
        .execute()
    
    logger.info(f"Disconnected calendar {calendar_id}")
    
    return {"message": "Calendar disconnected", "calendar_id": calendar_id}
