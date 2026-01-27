"""
Meeting Assistant - Transcription Worker
Consumes transcription jobs from Redis queue and processes with OpenAI Whisper API
"""
import asyncio
import json
import logging
import os
import tempfile
from datetime import datetime, timezone, timedelta
import math

import redis.asyncio as redis
from openai import OpenAI
from pydub import AudioSegment
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from supabase import create_client
from pathlib import Path

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


def format_timestamp(seconds: float) -> str:
    """Format seconds to HH:MM:SS"""
    td = timedelta(seconds=int(seconds))
    hours, remainder = divmod(td.seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if td.days > 0:
        hours += td.days * 24
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

class SpeakerAttributor:
    """Attributes speakers to transcription segments using captured captions"""
    
    def __init__(self, captions_path: str):
        self.captions = []
        if os.path.exists(captions_path):
            try:
                with open(captions_path, 'r') as f:
                    self.captions = json.load(f)
                logger.info(f"Loaded {len(self.captions)} caption segments for attribution")
            except Exception as e:
                logger.error(f"Failed to load captions: {e}")
    
    def get_speaker_at_time(self, timestamp_ms: int) -> str:
        """Get the speaker who was most likely active at a given timestamp"""
        if not self.captions:
            return None
        
        TIME_TOLERANCE_MS = 5000  # 5 second tolerance
        
        best_match = None
        best_score = float('inf')
        
        for seg in self.captions:
            # Check if timestamp falls within segment
            if seg['start_ms'] <= timestamp_ms <= seg['end_ms']:
                return seg['speaker']
            
            # Calculate distance to segment
            if timestamp_ms < seg['start_ms']:
                distance = seg['start_ms'] - timestamp_ms
            else:
                distance = timestamp_ms - seg['end_ms']
            
            # Keep track of closest segment within tolerance
            if distance < TIME_TOLERANCE_MS and distance < best_score:
                best_score = distance
                best_match = seg['speaker']
        
        return best_match

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
            
            # Format transcription with timestamps and speakers
            formatted_lines = []
            
            # Try to download and load captions for attribution
            captions_file = local_path.replace(".mp3", ".json")
            attributor = None
            
            try:
                captions_path = recording['storage_path'].replace(Path(recording['storage_path']).name, "captions.json")
                logger.info(f"Downloading captions from R2: {captions_path}")
                self.r2.download_file(R2_BUCKET_NAME, captions_path, captions_file)
                attributor = SpeakerAttributor(captions_file)
            except ClientError as e:
                if e.response['Error']['Code'] == "404":
                    logger.info("No captions.json found for this recording")
                else:
                    logger.warning(f"Error checking for captions: {e}")
            except Exception as e:
                logger.warning(f"Failed to setup speaker attribution: {e}")

            for segment in result.get("segments", []):
                start_time = segment.get("start", 0)
                start_ms = int(start_time * 1000)
                timestamp = format_timestamp(start_time)
                text = segment.get("text", "").strip()
                
                speaker_prefix = ""
                if attributor:
                    speaker = attributor.get_speaker_at_time(start_ms)
                    if speaker:
                        speaker_prefix = f" [{speaker}]"
                
                formatted_lines.append(f"[{timestamp}]{speaker_prefix} {text}")
            
            full_text = "\n".join(formatted_lines)
            word_count = len(full_text.split())
            
            # Parse start time and ensure it's timezone-aware
            start_time = datetime.fromisoformat(
                transcription["processing_started_at"].replace("Z", "+00:00")
            )
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)

            processing_time = int(
                (datetime.now(timezone.utc) - start_time).total_seconds()
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
            if 'captions_file' in locals() and os.path.exists(captions_file):
                os.unlink(captions_file)
    
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
        """Convert OpenAI response to database segment format with quality filtering"""
        segments = []
        MIN_CONFIDENCE = 0.4  # Minimum confidence threshold
        MIN_TEXT_LENGTH = 3   # Minimum text length
        
        for i, segment in enumerate(result.get("segments", [])):
            text = segment.get("text", "").strip()
            confidence = segment.get("confidence")
            
            # Skip empty or too short text
            if len(text) < MIN_TEXT_LENGTH:
                logger.debug(f"Skipping short segment: '{text}'")
                continue
            
            # Skip low confidence segments (if confidence is available)
            if confidence is not None and confidence < MIN_CONFIDENCE:
                logger.debug(f"Skipping low confidence segment ({confidence:.2f}): '{text}'")
                continue
            
            # Filter out hallucinated patterns
            if self._is_hallucination(text):
                logger.debug(f"Skipping hallucinated segment: '{text}'")
                continue
            
            segments.append({
                "transcription_id": transcription_id,
                "segment_index": len(segments),  # Re-index after filtering
                "start_time_ms": int(segment["start"] * 1000),
                "end_time_ms": int(segment["end"] * 1000),
                "text": text,
                "confidence": confidence,
                "words": segment.get("words")
            })
        
        return segments
    
    def _is_hallucination(self, text: str) -> bool:
        """Detect common Whisper hallucination patterns"""
        text_lower = text.lower().strip()
        
        # Common hallucination patterns in Portuguese and English
        hallucination_patterns = [
            "e aí",
            "oi",
            "obrigado por assistir",
            "obrigada por assistir",
            "se inscreva",
            "inscreva-se",
            "curta o vídeo",
            "like",
            "subscribe",
            "thanks for watching",
            "thank you for watching",
            "legenda automática",
            "legendas automáticas",
            "subtitles by",
            "subtítulos por",
            "copyright",
            "♪", "♫", "🎵",
            "...",
            "[música]",
            "[music]",
            "[aplausos]",
            "[risos]",
        ]
        
        # Check exact matches or starts with pattern
        for pattern in hallucination_patterns:
            if text_lower == pattern or text_lower == pattern + ".":
                return True
            # Check if the entire text is just the pattern repeated
            if text_lower.replace(".", "").replace(",", "").strip() == pattern:
                return True
        
        # Detect repetitive patterns like "E aí E aí E aí"
        words = text_lower.split()
        if len(words) >= 2:
            unique_words = set(words)
            # If very few unique words but many total words, likely repetitive
            if len(unique_words) <= 2 and len(words) >= 4:
                return True
        
        # Detect if text is just punctuation or symbols
        import re
        if re.match(r'^[\s\.\,\!\?\;\:\-\_\.\.\.]$', text):
            return True
        
        return False
    
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
