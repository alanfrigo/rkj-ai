"""
Meeting Assistant - Scheduler Service
Handles calendar sync and meeting scheduling
"""
import asyncio
import json
import logging
import os
import re
from datetime import datetime, timedelta
from typing import Optional

import redis.asyncio as redis
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from supabase import create_client

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
BOT_JOIN_BEFORE_MINUTES = int(os.getenv("BOT_JOIN_BEFORE_MINUTES", "2"))

# Calendar sync interval (seconds)
CALENDAR_SYNC_INTERVAL = 300  # 5 minutes
MEETING_CHECK_INTERVAL = 30  # 30 seconds

# Meeting URL patterns
MEET_PATTERN = re.compile(r'(https?://)?meet\.google\.com/[a-z]{3}-[a-z]{4}-[a-z]{3}', re.IGNORECASE)
ZOOM_PATTERN = re.compile(r'(https?://)?([\w-]+\.)?zoom\.us/(j|my)/[\w\d-]+', re.IGNORECASE)


class CalendarSync:
    """Handles Google Calendar synchronization"""
    
    def __init__(self, supabase, redis_client):
        self.supabase = supabase
        self.redis_client = redis_client
    
    async def sync_all_users(self):
        """Sync calendars for all users with connected Google Calendar"""
        logger.info("Starting calendar sync for all users")
        
        # Get all active users with Google refresh tokens and settings
        result = self.supabase.table('users')\
            .select('id, email, google_refresh_token, settings')\
            .not_.is_('google_refresh_token', 'null')\
            .execute()
        
        users = result.data or []
        logger.info(f"Found {len(users)} users with connected calendars")
        
        for user in users:
            try:
                # Check if user has auto sync enabled (default: True)
                settings = user.get('settings') or {}
                if not settings.get('auto_sync_calendar', True):
                    logger.info(f"Skipping sync for user {user['id']} - auto sync disabled")
                    continue
                
                await self.sync_user_calendar(user)
            except Exception as e:
                logger.error(f"Error syncing calendar for user {user['id']}: {e}")
    
    async def sync_user_calendar(self, user: dict):
        """Sync calendar for a single user"""
        user_id = user['id']
        refresh_token = user['google_refresh_token']
        
        logger.info(f"Syncing calendar for user {user_id}")
        
        # Build Google Calendar service
        credentials = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET
        )
        
        service = build('calendar', 'v3', credentials=credentials)
        
        # Get events for next 7 days
        now = datetime.utcnow()
        time_min = now.isoformat() + 'Z'
        time_max = (now + timedelta(days=7)).isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            maxResults=50,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        logger.info(f"Found {len(events)} events for user {user_id}")
        
        for event in events:
            await self.process_event(user_id, event)
    
    async def process_event(self, user_id: str, event: dict):
        """Process a single calendar event"""
        event_id = event['id']
        
        # Extract meeting URL
        meeting_url = self.extract_meeting_url(event)
        meeting_provider = self.detect_provider(meeting_url) if meeting_url else None
        should_record = meeting_url is not None
        
        # Parse times
        start = event.get('start', {})
        end = event.get('end', {})
        
        start_time = start.get('dateTime') or start.get('date')
        end_time = end.get('dateTime') or end.get('date')
        
        # Prepare event data
        event_data = {
            "user_id": user_id,
            "external_event_id": event_id,
            "title": event.get('summary', 'Untitled Meeting'),
            "description": event.get('description'),
            "start_time": start_time,
            "end_time": end_time,
            "meeting_url": meeting_url,
            "meeting_provider": meeting_provider,
            "organizer_email": event.get('organizer', {}).get('email'),
            "attendees": event.get('attendees', []),
            "status": 'confirmed' if event.get('status') == 'confirmed' else 'tentative', # Map to allowed status
            "should_record": should_record
        }
        
        # Upsert to database
        try:
            self.supabase.table('calendar_events').upsert(
                event_data,
                on_conflict='user_id,external_event_id'
            ).execute()
            logger.info(f"Processed event: {event_data['title']} (URL: {meeting_url})")
        except Exception as e:
            logger.error(f"Failed to upsert event {event_id}: {e}")
    
    def extract_meeting_url(self, event: dict) -> Optional[str]:
        """Extract meeting URL from event"""
        # Check conferenceData first (official Google Meet)
        conference_data = event.get('conferenceData', {})
        entry_points = conference_data.get('entryPoints', [])
        
        for entry in entry_points:
            if entry.get('entryPointType') == 'video':
                return entry.get('uri')
        
        # Check description and location for URLs
        description = event.get('description', '') or ''
        location = event.get('location', '') or ''
        text_to_search = f"{description} {location}"
        
        # Search for Meet URLs
        meet_match = MEET_PATTERN.search(text_to_search)
        if meet_match:
            url = meet_match.group()
            if not url.startswith('http'):
                url = f"https://{url}"
            return url
        
        # Search for Zoom URLs
        zoom_match = ZOOM_PATTERN.search(text_to_search)
        if zoom_match:
            url = zoom_match.group()
            if not url.startswith('http'):
                url = f"https://{url}"
            return url
        
        return None
    
    def detect_provider(self, url: str) -> str:
        """Detect meeting provider from URL"""
        if 'meet.google.com' in url:
            return 'google_meet'
        elif 'zoom.us' in url:
            return 'zoom'
        elif 'teams.microsoft.com' in url:
            return 'teams'
        else:
            return 'other'


class MeetingScheduler:
    """Handles meeting scheduling - triggers bots to join"""
    
    def __init__(self, supabase, redis_client):
        self.supabase = supabase
        self.redis_client = redis_client
    
    async def check_upcoming_meetings(self):
        """Check for meetings that need bots to join"""
        now = datetime.utcnow()
        join_window = now + timedelta(minutes=BOT_JOIN_BEFORE_MINUTES)
        
        # Find events that:
        # 1. Are about to start (start_time within join window) OR
        # 2. Have already started but not ended yet (ongoing meetings)
        # We use end_time > now to ensure the meeting is still happening
        # Note: We append 'Z' to indicate UTC timezone for proper comparison
        result = self.supabase.table('calendar_events')\
            .select('*')\
            .eq('should_record', True)\
            .eq('status', 'confirmed')\
            .lte('start_time', join_window.isoformat() + 'Z')\
            .gt('end_time', now.isoformat() + 'Z')\
            .execute()
        
        events = result.data or []
        
        if events:
            logger.info(f"Found {len(events)} meetings to potentially join")
        
        for event in events:
            await self.schedule_bot_join(event)
    
    async def schedule_bot_join(self, event: dict):
        """Schedule a bot to join a meeting"""
        event_id = event['id']
        user_id = event['user_id']
        
        # Check if meeting already exists
        existing = self.supabase.table('meetings')\
            .select('id')\
            .eq('calendar_event_id', event_id)\
            .execute().data
        
        if existing:
            logger.debug(f"Meeting already scheduled for event {event_id}")
            return
        
        # Fetch user settings for bot configuration
        user_result = self.supabase.table('users')\
            .select('settings')\
            .eq('id', user_id)\
            .single()\
            .execute()
        
        user_settings = user_result.data.get('settings', {}) if user_result.data else {}
        bot_display_name = user_settings.get('bot_display_name', 'RKJ.AI')
        bot_camera_enabled = user_settings.get('bot_camera_enabled', False)
        
        # Create meeting record
        meeting = self.supabase.table('meetings').insert({
            "user_id": user_id,
            "calendar_event_id": event_id,
            "title": event['title'],
            "meeting_url": event['meeting_url'],
            "meeting_provider": event['meeting_provider'],
            "status": "scheduled",
            "scheduled_start": event['start_time'],
            "scheduled_end": event['end_time']
        }).execute().data[0]
        
        meeting_id = meeting['id']
        logger.info(f"Created meeting {meeting_id} for event {event_id}")
        logger.info(f"  Bot Name: {bot_display_name}, Camera: {bot_camera_enabled}")
        
        # Enqueue bot join job
        job = {
            "id": meeting_id,
            "data": {
                "meeting_id": meeting_id,
                "meeting_url": event['meeting_url'],
                "meeting_provider": event['meeting_provider'],
                "user_id": user_id,
                "bot_display_name": bot_display_name,
                "bot_camera_enabled": bot_camera_enabled
            },
            "status": "queued",
            "created_at": datetime.utcnow().isoformat()
        }
        
        await self.redis_client.rpush("queue:join_meeting", json.dumps(job))
        logger.info(f"Enqueued bot join job for meeting {meeting_id}")


async def process_calendar_sync_queue(calendar_sync: CalendarSync, supabase, redis_client):
    """Process pending calendar sync jobs from the queue"""
    try:
        # Check for pending sync jobs (non-blocking)
        job_data = await redis_client.lpop("queue:calendar_sync")
        if not job_data:
            return
        
        job = json.loads(job_data)
        data = job.get("data", {})
        user_id = data.get("user_id")
        
        if not user_id:
            logger.error(f"Calendar sync job missing user_id: {job}")
            return
        
        logger.info(f"Processing manual calendar sync for user {user_id}")
        
        # Get user data
        result = supabase.table('users')\
            .select('id, email, google_refresh_token, settings')\
            .eq('id', user_id)\
            .single()\
            .execute()
        
        user = result.data
        if not user or not user.get('google_refresh_token'):
            logger.error(f"User {user_id} not found or no refresh token")
            return
        
        # Sync this user's calendar (bypass auto_sync check for manual syncs)
        await calendar_sync.sync_user_calendar(user)
        logger.info(f"Completed manual calendar sync for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error processing calendar sync job: {e}")


async def main():
    """Main entry point"""
    logger.info("Starting Scheduler service")
    
    # Initialize clients
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    await redis_client.ping()
    logger.info("Connected to Redis")
    
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    logger.info("Connected to Supabase")
    
    # Create sync and scheduler instances
    calendar_sync = CalendarSync(supabase, redis_client)
    meeting_scheduler = MeetingScheduler(supabase, redis_client)
    
    # Track last sync time
    last_calendar_sync = datetime.min
    
    try:
        while True:
            now = datetime.utcnow()
            
            # Process any pending manual calendar sync jobs
            await process_calendar_sync_queue(calendar_sync, supabase, redis_client)
            
            # Run calendar sync periodically (for auto-enabled users)
            if (now - last_calendar_sync).total_seconds() >= CALENDAR_SYNC_INTERVAL:
                await calendar_sync.sync_all_users()
                last_calendar_sync = now
            
            # Check for upcoming meetings more frequently
            await meeting_scheduler.check_upcoming_meetings()
            
            # Wait before next check
            await asyncio.sleep(MEETING_CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await redis_client.close()


if __name__ == "__main__":
    asyncio.run(main())

