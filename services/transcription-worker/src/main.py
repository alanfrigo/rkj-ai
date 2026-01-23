"""
Meeting Assistant - Transcription Worker
Consumes transcription jobs from Redis queue and processes with OpenAI Whisper API
"""
import asyncio
import json
import logging
import os
import tempfile
from datetime import datetime
import math

import redis.asyncio as redis
from openai import OpenAI
from pydub import AudioSegment
import boto3
from botocore.config import Config
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
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "meeting-assistant")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WHISPER_MODEL = os.getenv("OPENAI_WHISPER_MODEL", "whisper-1")

# OpenAI limits
MAX_FILE_SIZE_MB = 25
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
COST_PER_MINUTE_CENTS = 0.6  # $0.006 per minute

# Queue name
QUEUE_NAME = "queue:transcription"


class TranscriptionWorker:
    """Worker that processes transcription jobs"""
    
    def __init__(self):
        self.redis_client = None
        self.supabase = None
        self.openai = None
        self.r2 = None
    
    async def initialize(self):
        """Initialize all clients"""
        # Redis
        self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        await self.redis_client.ping()
        logger.info("Connected to Redis")
        
        # Supabase
        self.supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        logger.info("Connected to Supabase")
        
        # OpenAI
        self.openai = OpenAI(api_key=OPENAI_API_KEY)
        logger.info("OpenAI client initialized")
        
        # R2
        self.r2 = boto3.client(
            's3',
            endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY,
            config=Config(signature_version='s3v4'),
            region_name='auto'
        )
        logger.info("Connected to Cloudflare R2")
    
    async def run(self):
        """Main worker loop"""
        logger.info("Transcription worker started, waiting for jobs...")
        
        while True:
            try:
                # Blocking pop from queue
                result = await self.redis_client.blpop(QUEUE_NAME, timeout=30)
                
                if result:
                    _, job_json = result
                    job = json.loads(job_json)
                    
                    logger.info(f"Processing job: {job['id']}")
                    await self.process_job(job)
                    
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                await asyncio.sleep(5)
    
    async def process_job(self, job: dict):
        """Process a single transcription job"""
        job_id = job["id"]
        data = job["data"]
        
        meeting_id = data["meeting_id"]
        recording_id = data["recording_id"]
        language = data.get("language", "pt")
        
        logger.info(f"Transcribing meeting {meeting_id}, recording {recording_id}")
        
        # Get recording info
        recording = self.supabase.table('recordings')\
            .select('*')\
            .eq('id', recording_id)\
            .single()\
            .execute().data
        
        if not recording:
            logger.error(f"Recording not found: {recording_id}")
            return
        
        # Create transcription record
        transcription = self.supabase.table('transcriptions').insert({
            "meeting_id": meeting_id,
            "recording_id": recording_id,
            "language": language,
            "status": "processing",
            "model_used": WHISPER_MODEL,
            "processing_started_at": datetime.utcnow().isoformat()
        }).execute().data[0]
        
        transcription_id = transcription["id"]
        
        try:
            # Download audio from R2
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
                local_path = tmp_file.name
            
            logger.info(f"Downloading from R2: {recording['storage_path']}")
            self.r2.download_file(R2_BUCKET_NAME, recording['storage_path'], local_path)
            
            # Get audio duration
            audio = AudioSegment.from_file(local_path)
            duration_seconds = len(audio) / 1000
            logger.info(f"Audio duration: {duration_seconds:.2f} seconds")
            
            # Check file size and process
            file_size = os.path.getsize(local_path)
            
            if file_size > MAX_FILE_SIZE_BYTES:
                logger.info(f"File too large ({file_size / 1024 / 1024:.2f}MB), splitting...")
                result = await self.transcribe_large_file(local_path, audio, language)
            else:
                result = self.transcribe_file(local_path, language)
            
            # Calculate cost
            cost_cents = int(math.ceil(duration_seconds / 60) * COST_PER_MINUTE_CENTS)
            
            # Process and save segments
            segments = self.process_segments(result, transcription_id)
            
            if segments:
                self.supabase.table('transcription_segments').insert(segments).execute()
                logger.info(f"Saved {len(segments)} segments")
            
            # Update transcription record
            full_text = result.get("text", "")
            word_count = len(full_text.split())
            
            processing_time = int(
                (datetime.utcnow() - datetime.fromisoformat(
                    transcription["processing_started_at"].replace("Z", "")
                )).total_seconds()
            )
            
            self.supabase.table('transcriptions').update({
                "status": "completed",
                "full_text": full_text,
                "word_count": word_count,
                "audio_duration_seconds": int(duration_seconds),
                "cost_cents": cost_cents,
                "processing_completed_at": datetime.utcnow().isoformat(),
                "processing_duration_seconds": processing_time
            }).eq('id', transcription_id).execute()
            
            # Update meeting status
            self.supabase.table('meetings').update({
                "status": "completed"
            }).eq('id', meeting_id).execute()
            
            logger.info(f"Transcription completed: {transcription_id}")
            logger.info(f"Cost: ${cost_cents / 100:.2f}, Words: {word_count}")
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            
            self.supabase.table('transcriptions').update({
                "status": "failed",
                "error_message": str(e)
            }).eq('id', transcription_id).execute()
            
            self.supabase.table('meetings').update({
                "status": "failed",
                "error_message": f"Transcription failed: {str(e)}"
            }).eq('id', meeting_id).execute()
            
            raise
        
        finally:
            # Cleanup
            if 'local_path' in locals() and os.path.exists(local_path):
                os.unlink(local_path)
    
    def transcribe_file(self, file_path: str, language: str) -> dict:
        """Transcribe a single file using OpenAI Whisper API"""
        logger.info(f"Transcribing file: {file_path}")
        
        with open(file_path, "rb") as audio_file:
            response = self.openai.audio.transcriptions.create(
                model=WHISPER_MODEL,
                file=audio_file,
                language=language,
                response_format="verbose_json",
                timestamp_granularities=["segment", "word"]
            )
        
        return response.model_dump()
    
    async def transcribe_large_file(
        self,
        file_path: str,
        audio: AudioSegment,
        language: str
    ) -> dict:
        """Transcribe a large file by splitting into chunks"""
        total_duration_ms = len(audio)
        file_size = os.path.getsize(file_path)
        bytes_per_ms = file_size / total_duration_ms
        
        # Target 20MB per chunk
        target_chunk_bytes = 20 * 1024 * 1024
        chunk_duration_ms = int(target_chunk_bytes / bytes_per_ms)
        
        # Minimum 1 minute chunks
        chunk_duration_ms = max(chunk_duration_ms, 60 * 1000)
        
        logger.info(f"Splitting into {chunk_duration_ms / 1000 / 60:.1f} minute chunks")
        
        chunks = []
        start = 0
        while start < total_duration_ms:
            end = min(start + chunk_duration_ms, total_duration_ms)
            chunks.append((start, end))
            start = end
        
        logger.info(f"Processing {len(chunks)} chunks")
        
        all_segments = []
        all_words = []
        full_text_parts = []
        
        for i, (start_ms, end_ms) in enumerate(chunks):
            logger.info(f"Processing chunk {i + 1}/{len(chunks)}")
            
            # Extract chunk
            chunk_audio = audio[start_ms:end_ms]
            
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                chunk_path = tmp.name
            
            try:
                chunk_audio.export(chunk_path, format="mp3")
                
                # Transcribe chunk
                result = self.transcribe_file(chunk_path, language)
                
                # Adjust timestamps
                for segment in result.get("segments", []):
                    segment["start"] += start_ms / 1000
                    segment["end"] += start_ms / 1000
                    all_segments.append(segment)
                
                for word in result.get("words", []):
                    word["start"] += start_ms / 1000
                    word["end"] += start_ms / 1000
                    all_words.append(word)
                
                full_text_parts.append(result.get("text", ""))
                
            finally:
                if os.path.exists(chunk_path):
                    os.unlink(chunk_path)
        
        return {
            "text": " ".join(full_text_parts),
            "segments": all_segments,
            "words": all_words,
            "language": language
        }
    
    def process_segments(self, result: dict, transcription_id: str) -> list:
        """Convert OpenAI response to database segment format"""
        segments = []
        
        for i, segment in enumerate(result.get("segments", [])):
            segments.append({
                "transcription_id": transcription_id,
                "segment_index": i,
                "start_time_ms": int(segment["start"] * 1000),
                "end_time_ms": int(segment["end"] * 1000),
                "text": segment["text"].strip(),
                "confidence": segment.get("confidence"),
                "words": segment.get("words")
            })
        
        return segments
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.redis_client:
            await self.redis_client.close()


async def main():
    """Main entry point"""
    worker = TranscriptionWorker()
    
    try:
        await worker.initialize()
        await worker.run()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await worker.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
