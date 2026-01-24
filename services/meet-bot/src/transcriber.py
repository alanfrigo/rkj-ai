"""
Meet Bot - Transcriber
Transcribes audio using OpenAI Whisper API with timestamp formatting
"""
import asyncio
import logging
import os
import tempfile
from datetime import timedelta
from pathlib import Path
from typing import Optional

from openai import OpenAI
from pydub import AudioSegment

from .config import config

logger = logging.getLogger(__name__)

# OpenAI Whisper limits
MAX_FILE_SIZE_MB = 25
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


class Transcriber:
    """Handles audio transcription using OpenAI Whisper API"""
    
    def __init__(self):
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.OPENAI_WHISPER_MODEL
        self.language = config.TRANSCRIPTION_LANGUAGE
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds to HH:MM:SS"""
        td = timedelta(seconds=int(seconds))
        hours, remainder = divmod(td.seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        if td.days > 0:
            hours += td.days * 24
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def transcribe_file(self, file_path: str) -> dict:
        """Transcribe a single audio/video file using OpenAI Whisper API"""
        logger.info(f"Transcribing file: {file_path}")
        
        with open(file_path, "rb") as audio_file:
            response = self.client.audio.transcriptions.create(
                model=self.model,
                file=audio_file,
                language=self.language,
                response_format="verbose_json"
            )
        
        return response.model_dump()
    
    async def transcribe_large_file(self, file_path: str) -> dict:
        """Transcribe a large file by splitting into chunks"""
        audio = AudioSegment.from_file(file_path)
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
                result = self.transcribe_file(chunk_path)
                
                # Adjust timestamps
                for segment in result.get("segments", []):
                    segment["start"] += start_ms / 1000
                    segment["end"] += start_ms / 1000
                    all_segments.append(segment)
                
                full_text_parts.append(result.get("text", ""))
                
            finally:
                if os.path.exists(chunk_path):
                    os.unlink(chunk_path)
        
        return {
            "text": " ".join(full_text_parts),
            "segments": all_segments,
            "language": self.language
        }
    
    async def transcribe_audio(
        self, 
        recording_path: Path,
        caption_segments: list = None
    ) -> dict:
        """
        Transcribe audio from recording file
        
        Args:
            recording_path: Path to the video/audio recording
            caption_segments: Optional list of CaptionSegment objects from live captions
            
        Returns:
            dict with 'text', 'segments', 'formatted', and optionally 'speakers' keys
        """
        logger.info(f"Starting transcription for: {recording_path}")
        
        if not recording_path.exists():
            raise FileNotFoundError(f"Recording not found: {recording_path}")
        
        file_size = recording_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        logger.info(f"File size: {file_size_mb:.2f} MB")
        
        # Transcribe based on file size
        if file_size > MAX_FILE_SIZE_BYTES:
            logger.info(f"File too large ({file_size_mb:.2f}MB), splitting...")
            result = await self.transcribe_large_file(str(recording_path))
        else:
            result = self.transcribe_file(str(recording_path))
        
        # Build speaker lookup from caption segments with time tolerance
        # Caption timestamps may not align perfectly with Whisper timestamps
        TIME_TOLERANCE_MS = 5000  # 5 second tolerance window
        
        def get_speaker_at_time(timestamp_ms: int) -> str:
            """Get the speaker who was most likely active at a given timestamp"""
            if not caption_segments:
                return None
            
            best_match = None
            best_score = float('inf')
            
            for seg in caption_segments:
                # Check if timestamp falls within segment
                if seg.start_ms <= timestamp_ms <= seg.end_ms:
                    return seg.speaker  # Direct match
                
                # Calculate distance to segment
                if timestamp_ms < seg.start_ms:
                    distance = seg.start_ms - timestamp_ms
                else:
                    distance = timestamp_ms - seg.end_ms
                
                # Keep track of closest segment within tolerance
                if distance < TIME_TOLERANCE_MS and distance < best_score:
                    best_score = distance
                    best_match = seg.speaker
            
            # If no match within tolerance, use the most recent speaker before this time
            if not best_match:
                for seg in reversed(caption_segments):
                    if seg.end_ms <= timestamp_ms + TIME_TOLERANCE_MS:
                        return seg.speaker
            
            return best_match
        
        # Format transcription with timestamps and speakers
        formatted_lines = []
        speakers_found = set()
        
        # Also extract speakers from caption segments
        if caption_segments:
            for seg in caption_segments:
                speakers_found.add(seg.speaker)
        
        for segment in result.get("segments", []):
            start_time_sec = segment.get("start", 0)
            start_time_ms = int(start_time_sec * 1000)
            timestamp_str = self._format_timestamp(start_time_sec)
            text = segment.get("text", "").strip()
            
            if text:
                speaker = get_speaker_at_time(start_time_ms)
                if speaker:
                    formatted_lines.append(f"[{timestamp_str}] [{speaker}] {text}")
                    segment["speaker"] = speaker  # Add to segment data
                else:
                    formatted_lines.append(f"[{timestamp_str}] {text}")
        
        result["formatted"] = "\n".join(formatted_lines)
        result["speakers"] = list(speakers_found)
        
        word_count = len(result.get("text", "").split())
        speaker_count = len(speakers_found)
        logger.info(f"Transcription completed: {word_count} words, {len(result.get('segments', []))} segments, {speaker_count} speakers identified")
        
        return result
    
    def save_transcription_file(
        self, 
        result: dict, 
        output_path: Path,
        include_full_text: bool = True
    ) -> Path:
        """
        Save transcription to a text file
        
        Args:
            result: Transcription result from transcribe_audio
            output_path: Where to save the file
            include_full_text: Whether to include full text at the end
            
        Returns:
            Path to the saved file
        """
        logger.info(f"Saving transcription to: {output_path}")
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            # Header
            f.write("=" * 60 + "\n")
            f.write("TRANSCRIPTION\n")
            f.write(f"Language: {result.get('language', 'unknown')}\n")
            word_count = len(result.get("text", "").split())
            f.write(f"Words: {word_count}\n")
            
            # Speakers list
            speakers = result.get("speakers", [])
            if speakers:
                f.write(f"Speakers: {', '.join(speakers)}\n")
            
            f.write("=" * 60 + "\n\n")
            
            # Timestamped segments
            f.write(result.get("formatted", ""))
            
            # Full text at end (optional)
            if include_full_text:
                f.write("\n\n")
                f.write("=" * 60 + "\n")
                f.write("FULL TEXT\n")
                f.write("=" * 60 + "\n\n")
                f.write(result.get("text", ""))
        
        logger.info(f"Transcription saved: {output_path}")
        return output_path
