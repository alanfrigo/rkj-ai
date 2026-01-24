"""
Meet Bot - Main Entry Point
"""
import asyncio
import json
import logging
import os
import signal
import sys
from datetime import datetime

import redis.asyncio as redis
from supabase import create_client

from .config import config
from .bot import MeetBot
from .transcriber import Transcriber

# Global reference for signal handlers
_bot_instance = None
_shutdown_requested = False

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Exit codes
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_JOIN_FAILED = 2
EXIT_TIMEOUT = 3
EXIT_RECORDING_ERROR = 4
EXIT_UPLOAD_ERROR = 5


DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"


async def update_meeting_status(supabase, meeting_id: str, status: str, **kwargs):
    """Update meeting status in database"""
    if DRY_RUN:
        logger.info(f"[DRY_RUN] Would update meeting {meeting_id} to status: {status}")
        return
    update_data = {"status": status, "updated_at": datetime.utcnow().isoformat()}
    update_data.update(kwargs)
    
    supabase.table('meetings').update(update_data).eq('id', meeting_id).execute()
    logger.info(f"Updated meeting {meeting_id} status to: {status}")


async def create_recording_record(supabase, meeting_id: str, storage_path: str, duration: int) -> str:
    """Create recording record in database"""
    if DRY_RUN:
        logger.info(f"[DRY_RUN] Would create recording for meeting {meeting_id}")
        return "dry-run-recording-id"
    recording = supabase.table('recordings').insert({
        "meeting_id": meeting_id,
        "file_type": "combined",
        "file_name": os.path.basename(storage_path),
        "storage_path": storage_path,
        "duration_seconds": duration,
        "format": "mp4",
        "is_processed": True
    }).execute().data[0]
    
    logger.info(f"Created recording record: {recording['id']}")
    return recording['id']


async def enqueue_transcription(redis_client, meeting_id: str, recording_id: str, user_id: str):
    """Enqueue transcription job"""
    if DRY_RUN:
        logger.info(f"[DRY_RUN] Would enqueue transcription for meeting {meeting_id}")
        return
    job = {
        "id": f"transcribe_{meeting_id}",
        "data": {
            "meeting_id": meeting_id,
            "recording_id": recording_id,
            "language": "pt",
            "user_id": user_id
        },
        "status": "queued",
        "created_at": datetime.utcnow().isoformat()
    }
    
    await redis_client.rpush("queue:transcription", json.dumps(job))
    logger.info(f"Enqueued transcription job for meeting {meeting_id}")


def handle_shutdown_signal(signum, frame):
    """Handle shutdown signals (SIGINT, SIGTERM) gracefully"""
    global _shutdown_requested
    signal_name = signal.Signals(signum).name
    logger.info(f"Received {signal_name}, initiating graceful shutdown...")
    _shutdown_requested = True


async def main():
    """Main entry point"""
    global _bot_instance, _shutdown_requested

    logger.info("=" * 50)
    logger.info("Meet Bot Starting")
    logger.info("=" * 50)

    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_shutdown_signal)
    signal.signal(signal.SIGTERM, handle_shutdown_signal)

    # Get meeting info from environment
    meeting_url = config.MEETING_URL
    meeting_id = config.MEETING_ID
    user_id = config.USER_ID

    if not meeting_url or not meeting_id:
        logger.error("MEETING_URL and MEETING_ID are required")
        sys.exit(EXIT_ERROR)

    logger.info(f"Meeting ID: {meeting_id}")
    logger.info(f"Meeting URL: {meeting_url}")
    logger.info(f"User ID: {user_id}")

    # Initialize clients
    supabase = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)
    redis_client = redis.from_url(config.REDIS_URL, decode_responses=True)

    # Create bot
    bot = MeetBot(meeting_id, meeting_url, user_id)
    _bot_instance = bot  # Store global reference for signal handler

    exit_code = EXIT_SUCCESS
    recording_path = None
    is_uploaded = False
    
    try:
        # Update status to joining
        await update_meeting_status(supabase, meeting_id, "joining")

        # Start browser
        await bot.start()

        # Early recording mode: start recording before confirming join
        # This captures the waiting room and any issues during join
        if config.EARLY_RECORDING_MODE:
            logger.info("Early recording mode enabled - starting recording before join")
            await bot.start_recording()

        # Join meeting
        if not await bot.join_meeting():
            logger.error("Failed to join meeting")

            # If early recording was on, we might have captured useful debug info
            if config.EARLY_RECORDING_MODE:
                logger.info("Stopping early recording due to join failure")
                try:
                    recording_path = await bot.stop_recording()
                    if recording_path:
                        logger.info(f"Early recording saved to: {recording_path}")
                except Exception as e:
                    logger.warning(f"Could not save early recording: {e}")

            await update_meeting_status(
                supabase, meeting_id, "failed",
                error_message="Failed to join meeting"
            )
            exit_code = EXIT_JOIN_FAILED
            return

        # Update status to recording
        await update_meeting_status(
            supabase, meeting_id, "recording",
            actual_start=datetime.utcnow().isoformat()
        )

        # Start recording immediately if not already started
        if not config.EARLY_RECORDING_MODE:
            logger.info("Join confirmed - Starting recording immediately")
            await bot.start_recording()

        # Monitor meeting until it ends OR shutdown signal received
        logger.info("Monitoring meeting (Ctrl+C to stop and save recording)...")

        async def monitor_with_shutdown():
            """Monitor meeting with shutdown signal check"""
            global _shutdown_requested
            check_count = 0
            while bot.is_in_meeting and not bot.meeting_ended:
                check_count += 1

                # Check for shutdown signal
                if _shutdown_requested:
                    logger.info("Shutdown signal received, stopping recording...")
                    return

                # Check if meeting ended
                if await bot._check_meeting_ended():
                    logger.info("Meeting ended detected")
                    bot.meeting_ended = True
                    return

                # Check max duration
                if await bot.recorder.is_max_duration_reached():
                    logger.info("Max duration reached")
                    bot.meeting_ended = True
                    return

                # Log status periodically (every 30 seconds)
                if check_count % 15 == 0:
                    duration = bot.recorder.get_duration_seconds() if bot.recorder else 0
                    logger.info(f"Still recording... Duration: {duration}s")

                await asyncio.sleep(2)

        await monitor_with_shutdown()

        # Stop recording
        logger.info("Stopping recording...")
        recording_path = await bot.stop_recording()
        
        if not recording_path:
            logger.error("Recording failed - no file produced")
            await update_meeting_status(
                supabase, meeting_id, "failed",
                error_message="Recording failed"
            )
            exit_code = EXIT_RECORDING_ERROR
            return
        
        # Update status to processing
        await update_meeting_status(
            supabase, meeting_id, "processing",
            actual_end=datetime.utcnow().isoformat(),
            duration_seconds=bot.get_duration_seconds()
        )
        
        # Leave meeting
        await bot.leave_meeting()
        
        # Upload recording
        try:
            storage_path = await bot.upload_recording(recording_path)
            is_uploaded = True
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            await update_meeting_status(
                supabase, meeting_id, "failed",
                error_message=f"Upload failed: {str(e)}"
            )
            exit_code = EXIT_UPLOAD_ERROR
            return
        
        # Transcribe recording directly (before database operations for DRY_RUN compatibility)
        await update_meeting_status(supabase, meeting_id, "transcribing")
        
        transcription_path = None
        try:
            if config.OPENAI_API_KEY:
                logger.info("Starting transcription...")
                transcriber = Transcriber()
                
                # Get caption segments with speaker info (from live captions)
                caption_segments = None
                if bot.caption_scraper:
                    caption_segments = bot.caption_scraper.get_segments()
                    logger.info(f"Caption data: {len(caption_segments)} segments captured with speaker names")
                
                # Transcribe the audio with speaker info from captions
                transcription_result = await transcriber.transcribe_audio(
                    recording_path, 
                    caption_segments=caption_segments
                )
                
                # Save transcription file locally
                transcription_path = recording_path.parent / "transcription.txt"
                transcriber.save_transcription_file(transcription_result, transcription_path)
                
                # Upload to R2
                transcription_storage_path = bot.uploader.upload_transcription(
                    transcription_path,
                    user_id,
                    meeting_id
                )
                logger.info(f"Transcription uploaded: {transcription_storage_path}")
            else:
                logger.warning("OPENAI_API_KEY not set, skipping transcription")
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            import traceback
            traceback.print_exc()
            # Don't fail the whole process, just log and continue
        
        # Create recording record (may fail in DRY_RUN mode, but that's ok)
        try:
            recording_id = await create_recording_record(
                supabase,
                meeting_id,
                storage_path,
                bot.get_duration_seconds()
            )
            
            # Enqueue transcription job for worker (if not already transcribed)
            if not transcription_path:
                await enqueue_transcription(redis_client, meeting_id, recording_id, user_id)
        except Exception as e:
            logger.warning(f"Database record creation failed (ok in DRY_RUN mode): {e}")
        
        # Update meeting status to completed
        await update_meeting_status(supabase, meeting_id, "completed")
        
        logger.info("=" * 50)
        logger.info("Bot completed successfully!")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.exception(f"Bot error: {e}")

        try:
            await update_meeting_status(
                supabase, meeting_id, "failed",
                error_message=str(e)
            )
        except Exception:
            pass
        exit_code = EXIT_ERROR

    finally:
        # Ensure recording is stopped and saved
        try:
            if bot.recorder and bot.recorder.is_recording:
                logger.info("Ensuring recording is stopped...")
                final_path = await bot.stop_recording()
                if final_path:
                    recording_path = final_path
                    logger.info(f"Recording saved in finally block: {recording_path}")
            
            # Emergency upload if we have a file but haven't uploaded it successfully yet
            if recording_path and not is_uploaded and os.path.exists(recording_path) and os.path.getsize(recording_path) > 0:
                logger.info("Attempting emergency upload in finally block...")
                try:
                    storage_path = await bot.upload_recording(recording_path)
                    logger.info(f"Emergency upload successful: {storage_path}")
                    
                    # Try to maintain data integrity if possible
                    try:
                         # Create recording record so it's not lost
                        await create_recording_record(
                            supabase,
                            meeting_id,
                            storage_path,
                            bot.recorder.get_duration_seconds()
                        )
                    except Exception as db_err:
                        logger.error(f"Could not create DB record for emergency upload: {db_err}")

                except Exception as upload_err:
                    logger.error(f"Emergency upload failed: {upload_err}")

        except Exception as e:
            logger.warning(f"Error in finally block: {e}")

        await bot.cleanup()
        await redis_client.aclose()
        sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
