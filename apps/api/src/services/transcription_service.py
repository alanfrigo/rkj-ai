"""
Meeting Assistant - Transcription Service
OpenAI Whisper API integration for audio transcription
"""
import os
import tempfile
from typing import Optional
from datetime import datetime
import logging
from openai import OpenAI
from pydub import AudioSegment
import math

from ..config import settings
from ..core.r2 import get_r2_storage
from ..core.supabase import get_db

logger = logging.getLogger(__name__)

# OpenAI Whisper limits
MAX_FILE_SIZE_MB = 25
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
COST_PER_MINUTE_CENTS = 0.6  # $0.006 per minute


class TranscriptionService:
    """Service for transcribing audio using OpenAI Whisper API"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.r2 = get_r2_storage()
        self.db = get_db(admin=True)
        self.model = settings.OPENAI_WHISPER_MODEL
    
    async def transcribe_meeting(
        self,
        meeting_id: str,
        recording_id: str,
        language: str = "pt"
    ) -> dict:
        """
        Transcribe a meeting recording
        
        Args:
            meeting_id: Meeting ID
            recording_id: Recording ID to transcribe
            language: Language code (default: Portuguese)
        
        Returns:
            Transcription result dict
        """
        logger.info(f"Starting transcription for meeting {meeting_id}")
        
        # Get recording info
        recording = self.db.get_recording(recording_id)
        if not recording:
            raise ValueError(f"Recording not found: {recording_id}")
        
        # Create transcription record
        transcription = self.db.create_transcription({
            "meeting_id": meeting_id,
            "recording_id": recording_id,
            "language": language,
            "status": "processing",
            "model_used": self.model,
            "processing_started_at": datetime.utcnow().isoformat()
        })
        
        transcription_id = transcription["id"]
        
        try:
            # Download audio from R2
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
                local_path = tmp_file.name
            
            logger.info(f"Downloading audio from R2: {recording['storage_path']}")
            self.r2.download_file(recording['storage_path'], local_path)
            
            # Get audio duration
            audio = AudioSegment.from_file(local_path)
            duration_seconds = len(audio) / 1000
            logger.info(f"Audio duration: {duration_seconds:.2f} seconds")
            
            # Check file size and split if necessary
            file_size = os.path.getsize(local_path)
            
            if file_size > MAX_FILE_SIZE_BYTES:
                logger.info(f"File size ({file_size / 1024 / 1024:.2f}MB) exceeds limit, splitting...")
                transcription_result = await self._transcribe_large_file(
                    local_path, audio, language
                )
            else:
                transcription_result = await self._transcribe_file(
                    local_path, language
                )
            
            # Calculate cost
            cost_cents = int(math.ceil(duration_seconds / 60) * COST_PER_MINUTE_CENTS)
            
            # Process segments
            segments = self._process_segments(
                transcription_result,
                transcription_id
            )
            
            # Save segments to database
            if segments:
                self.db.create_transcription_segments(segments)
            
            # Update transcription record
            full_text = transcription_result.get("text", "")
            word_count = len(full_text.split())
            
            self.db.update_transcription(transcription_id, {
                "status": "completed",
                "full_text": full_text,
                "word_count": word_count,
                "audio_duration_seconds": int(duration_seconds),
                "cost_cents": cost_cents,
                "processing_completed_at": datetime.utcnow().isoformat(),
                "processing_duration_seconds": int(
                    (datetime.utcnow() - datetime.fromisoformat(
                        transcription["processing_started_at"].replace("Z", "")
                    )).total_seconds()
                )
            })
            
            # Update meeting status
            self.db.update_meeting(meeting_id, {"status": "completed"})
            
            logger.info(f"Transcription completed: {transcription_id}")
            
            return {
                "transcription_id": transcription_id,
                "full_text": full_text,
                "word_count": word_count,
                "segments_count": len(segments),
                "duration_seconds": int(duration_seconds),
                "cost_cents": cost_cents
            }
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            
            self.db.update_transcription(transcription_id, {
                "status": "failed",
                "error_message": str(e)
            })
            
            self.db.update_meeting(meeting_id, {
                "status": "failed",
                "error_message": f"Transcription failed: {str(e)}"
            })
            
            raise
        
        finally:
            # Cleanup temp file
            if 'local_path' in locals() and os.path.exists(local_path):
                os.unlink(local_path)
    
    async def _transcribe_file(
        self,
        file_path: str,
        language: str
    ) -> dict:
        """
        Transcribe a single audio file
        
        Returns:
            OpenAI transcription response
        """
        logger.info(f"Transcribing file: {file_path}")
        
        with open(file_path, "rb") as audio_file:
            response = self.client.audio.transcriptions.create(
                model=self.model,
                file=audio_file,
                language=language,
                response_format="verbose_json",
                timestamp_granularities=["segment", "word"]
            )
        
        return response.model_dump()
    
    async def _transcribe_large_file(
        self,
        file_path: str,
        audio: AudioSegment,
        language: str
    ) -> dict:
        """
        Transcribe a large file by splitting into chunks
        
        Args:
            file_path: Path to audio file
            audio: Loaded AudioSegment
            language: Language code
        
        Returns:
            Combined transcription result
        """
        # Calculate chunk duration (aim for ~20MB chunks)
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
                result = await self._transcribe_file(chunk_path, language)
                
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
    
    def _process_segments(
        self,
        transcription_result: dict,
        transcription_id: str
    ) -> list:
        """
        Convert OpenAI response to database segment format
        
        Args:
            transcription_result: OpenAI API response
            transcription_id: Database transcription ID
        
        Returns:
            List of segment dicts for database insertion
        """
        segments = []
        
        for i, segment in enumerate(transcription_result.get("segments", [])):
            segments.append({
                "transcription_id": transcription_id,
                "segment_index": i,
                "start_time_ms": int(segment["start"] * 1000),
                "end_time_ms": int(segment["end"] * 1000),
                "text": segment["text"].strip(),
                "confidence": segment.get("confidence"),
                # Store word-level timestamps if available
                "words": segment.get("words")
            })
        
        return segments
    
    async def get_transcription_with_segments(
        self,
        transcription_id: str
    ) -> Optional[dict]:
        """Get full transcription with all segments"""
        return self.db.get_transcription(transcription_id)
    
    async def search_transcriptions(
        self,
        user_id: str,
        query: str,
        limit: int = 20
    ) -> list:
        """
        Search across all user's transcriptions
        
        Args:
            user_id: User ID
            query: Search query
            limit: Max results
        
        Returns:
            List of matching segments with meeting info
        """
        # Use the database function for full-text search
        db = get_db(admin=True)
        
        result = db.client.rpc(
            'search_transcriptions',
            {
                'p_user_id': user_id,
                'p_query': query,
                'p_limit': limit
            }
        ).execute()
        
        return result.data or []


# Singleton instance
_transcription_service: Optional[TranscriptionService] = None


def get_transcription_service() -> TranscriptionService:
    """Get transcription service singleton"""
    global _transcription_service
    if _transcription_service is None:
        _transcription_service = TranscriptionService()
    return _transcription_service
