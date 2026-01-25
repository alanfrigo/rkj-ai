"""
Meeting Assistant - Settings Router
API endpoints for user settings and preferences
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Optional
import logging

from ..core.supabase import get_db
from ..core.redis import enqueue_job, Queues
from ..dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/preferences")
async def get_preferences(
    user: dict = Depends(get_current_user)
):
    """
    Get current user preferences/settings
    """
    db = get_db(admin=True)
    
    result = db.client.table('users')\
        .select('settings')\
        .eq('id', user["id"])\
        .single()\
        .execute()
    
    settings = result.data.get('settings', {}) if result.data else {}
    
    # Ensure defaults are present
    defaults = {
        "auto_record": True,
        "default_language": "pt-BR",
        "notifications_enabled": True,
        "email_notifications": True,
        "auto_sync_calendar": True
    }
    
    # Merge defaults with existing settings
    for key, value in defaults.items():
        if key not in settings:
            settings[key] = value
    
    return {"settings": settings}


@router.patch("/preferences")
async def update_preferences(
    auto_sync_calendar: Optional[bool] = Body(None, embed=False),
    auto_record: Optional[bool] = Body(None, embed=False),
    email_notifications: Optional[bool] = Body(None, embed=False),
    notifications_enabled: Optional[bool] = Body(None, embed=False),
    user: dict = Depends(get_current_user)
):
    """
    Update user preferences
    
    When auto_sync_calendar changes from False to True, 
    triggers an immediate calendar sync.
    """
    db = get_db(admin=True)
    
    # Get current settings
    current = db.client.table('users')\
        .select('settings')\
        .eq('id', user["id"])\
        .single()\
        .execute()
    
    current_settings = current.data.get('settings', {}) if current.data else {}
    was_sync_disabled = not current_settings.get('auto_sync_calendar', True)
    
    # Build updates object (only include provided values)
    updates = {}
    if auto_sync_calendar is not None:
        updates['auto_sync_calendar'] = auto_sync_calendar
    if auto_record is not None:
        updates['auto_record'] = auto_record
    if email_notifications is not None:
        updates['email_notifications'] = email_notifications
    if notifications_enabled is not None:
        updates['notifications_enabled'] = notifications_enabled
    
    if not updates:
        return {"settings": current_settings, "sync_triggered": False}
    
    # Merge with existing settings
    new_settings = {**current_settings, **updates}
    
    # Update database
    result = db.client.table('users')\
        .update({"settings": new_settings})\
        .eq('id', user["id"])\
        .execute()
    
    sync_triggered = False
    
    # If sync was disabled and is now enabled, trigger immediate sync
    if was_sync_disabled and updates.get('auto_sync_calendar', False):
        try:
            job_id = await enqueue_job(Queues.CALENDAR_SYNC, {
                "user_id": user["id"],
                "immediate": True
            })
            logger.info(f"Triggered immediate calendar sync for user {user['id']}, job_id: {job_id}")
            sync_triggered = True
        except Exception as e:
            logger.error(f"Failed to trigger immediate sync: {e}")
    
    logger.info(f"Updated preferences for user {user['id']}: {updates}")
    
    return {
        "settings": new_settings,
        "sync_triggered": sync_triggered
    }
