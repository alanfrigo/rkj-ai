"""
Meeting Assistant - Supabase Client
Database and authentication client
"""
from supabase import create_client, Client
from typing import Optional
import logging

from ..config import settings

logger = logging.getLogger(__name__)

# Global Supabase clients
_supabase_client: Optional[Client] = None
_supabase_admin: Optional[Client] = None


def get_supabase() -> Client:
    """
    Get Supabase client with anon key
    Use for operations that should respect RLS
    """
    global _supabase_client
    
    if _supabase_client is None:
        _supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY
        )
        logger.info("Supabase client initialized (anon)")
    
    return _supabase_client


def get_supabase_admin() -> Client:
    """
    Get Supabase client with service role key
    Use for backend operations that bypass RLS
    """
    global _supabase_admin
    
    if _supabase_admin is None:
        _supabase_admin = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_KEY
        )
        logger.info("Supabase admin client initialized (service role)")
    
    return _supabase_admin


async def get_user_from_token(token: str) -> Optional[dict]:
    """
    Validate JWT token and get user info
    
    Args:
        token: JWT token from Authorization header
    
    Returns:
        User dict or None if invalid
    """
    try:
        client = get_supabase()
        response = client.auth.get_user(token)
        
        if response and response.user:
            return {
                "id": response.user.id,
                "email": response.user.email,
                "user_metadata": response.user.user_metadata
            }
        return None
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        return None


# Database helper functions
class Database:
    """Database operations helper"""
    
    def __init__(self, admin: bool = False):
        """
        Args:
            admin: Use service role (bypass RLS) if True
        """
        self.client = get_supabase_admin() if admin else get_supabase()
    
    # -------------------------------------------
    # Users
    # -------------------------------------------
    def get_user(self, user_id: str) -> Optional[dict]:
        """Get user by ID"""
        result = self.client.table('users')\
            .select('*')\
            .eq('id', user_id)\
            .single()\
            .execute()
        return result.data
    
    def update_user(self, user_id: str, data: dict) -> dict:
        """Update user"""
        result = self.client.table('users')\
            .update(data)\
            .eq('id', user_id)\
            .execute()
        return result.data[0] if result.data else None
    
    # -------------------------------------------
    # Calendar Events
    # -------------------------------------------
    def get_upcoming_events(self, user_id: str, hours: int = 24) -> list:
        """Get upcoming calendar events with meeting URLs"""
        from datetime import datetime, timedelta
        
        now = datetime.utcnow()
        end_time = now + timedelta(hours=hours)
        
        result = self.client.table('calendar_events')\
            .select('*')\
            .eq('user_id', user_id)\
            .eq('should_record', True)\
            .eq('status', 'confirmed')\
            .gte('start_time', now.isoformat())\
            .lte('start_time', end_time.isoformat())\
            .order('start_time')\
            .execute()
        
        return result.data or []
    
    def upsert_calendar_event(self, event: dict) -> dict:
        """Insert or update calendar event"""
        result = self.client.table('calendar_events')\
            .upsert(event, on_conflict='user_id,external_event_id')\
            .execute()
        return result.data[0] if result.data else None
    
    # -------------------------------------------
    # Meetings
    # -------------------------------------------
    def create_meeting(self, meeting: dict) -> dict:
        """Create a new meeting"""
        result = self.client.table('meetings')\
            .insert(meeting)\
            .execute()
        return result.data[0] if result.data else None
    
    def get_meeting(self, meeting_id: str) -> Optional[dict]:
        """Get meeting by ID"""
        result = self.client.table('meetings')\
            .select('*, recordings(*), transcriptions(*)')\
            .eq('id', meeting_id)\
            .single()\
            .execute()
        return result.data
    
    def get_user_meetings(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> list:
        """Get meetings for a user"""
        query = self.client.table('meetings')\
            .select('*, recordings(id, file_type, storage_url, duration_seconds)')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .range(offset, offset + limit - 1)
        
        if status:
            query = query.eq('status', status)
        
        result = query.execute()
        return result.data or []
    
    def update_meeting(self, meeting_id: str, data: dict) -> dict:
        """Update meeting"""
        result = self.client.table('meetings')\
            .update(data)\
            .eq('id', meeting_id)\
            .execute()
        return result.data[0] if result.data else None
    
    def get_scheduled_meetings(self, minutes_ahead: int = 5) -> list:
        """Get meetings scheduled to start soon (for scheduler)"""
        from datetime import datetime, timedelta
        
        now = datetime.utcnow()
        window_end = now + timedelta(minutes=minutes_ahead)
        
        result = self.client.table('meetings')\
            .select('*')\
            .eq('status', 'scheduled')\
            .gte('scheduled_start', now.isoformat())\
            .lte('scheduled_start', window_end.isoformat())\
            .execute()
        
        return result.data or []
    
    # -------------------------------------------
    # Recordings
    # -------------------------------------------
    def create_recording(self, recording: dict) -> dict:
        """Create a new recording"""
        result = self.client.table('recordings')\
            .insert(recording)\
            .execute()
        return result.data[0] if result.data else None
    
    def get_recording(self, recording_id: str) -> Optional[dict]:
        """Get recording by ID"""
        result = self.client.table('recordings')\
            .select('*')\
            .eq('id', recording_id)\
            .single()\
            .execute()
        return result.data
    
    def update_recording(self, recording_id: str, data: dict) -> dict:
        """Update recording"""
        result = self.client.table('recordings')\
            .update(data)\
            .eq('id', recording_id)\
            .execute()
        return result.data[0] if result.data else None
    
    # -------------------------------------------
    # Transcriptions
    # -------------------------------------------
    def create_transcription(self, transcription: dict) -> dict:
        """Create a new transcription"""
        result = self.client.table('transcriptions')\
            .insert(transcription)\
            .execute()
        return result.data[0] if result.data else None
    
    def get_transcription(self, transcription_id: str) -> Optional[dict]:
        """Get transcription with segments"""
        result = self.client.table('transcriptions')\
            .select('*, transcription_segments(*)')\
            .eq('id', transcription_id)\
            .single()\
            .execute()
        return result.data
    
    def get_meeting_transcription(self, meeting_id: str) -> Optional[dict]:
        """Get transcription for a meeting"""
        result = self.client.table('transcriptions')\
            .select('*, transcription_segments(*)')\
            .eq('meeting_id', meeting_id)\
            .single()\
            .execute()
        return result.data
    
    def update_transcription(self, transcription_id: str, data: dict) -> dict:
        """Update transcription"""
        result = self.client.table('transcriptions')\
            .update(data)\
            .eq('id', transcription_id)\
            .execute()
        return result.data[0] if result.data else None
    
    def create_transcription_segments(self, segments: list) -> list:
        """Bulk insert transcription segments"""
        result = self.client.table('transcription_segments')\
            .insert(segments)\
            .execute()
        return result.data or []
    
    # -------------------------------------------
    # Processing Jobs
    # -------------------------------------------
    def create_job(self, job: dict) -> dict:
        """Create a processing job"""
        result = self.client.table('processing_jobs')\
            .insert(job)\
            .execute()
        return result.data[0] if result.data else None
    
    def update_job(self, job_id: str, data: dict) -> dict:
        """Update processing job"""
        result = self.client.table('processing_jobs')\
            .update(data)\
            .eq('id', job_id)\
            .execute()
        return result.data[0] if result.data else None


# Helper to get database instance
def get_db(admin: bool = False) -> Database:
    """Get database helper instance"""
    return Database(admin=admin)
