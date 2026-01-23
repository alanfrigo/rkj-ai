"""
Meet Bot - FFmpeg Recorder
Handles screen and audio recording using FFmpeg
"""
import asyncio
import logging
import os
import signal
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import config

logger = logging.getLogger(__name__)


class Recorder:
    """Handles recording of screen and audio using FFmpeg"""
    
    def __init__(self, meeting_id: str):
        self.meeting_id = meeting_id
        self.process: Optional[asyncio.subprocess.Process] = None
        self.recording_path: Optional[Path] = None
        self.is_recording = False
        self.start_time: Optional[datetime] = None
    
    def _get_output_path(self) -> Path:
        """Generate output file path"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"meeting_{self.meeting_id}_{timestamp}.mp4"
        return Path(config.RECORDING_DIR) / filename
    
    def _build_ffmpeg_command(self, output_path: Path) -> list:
        """Build FFmpeg command for recording"""
        settings = config.get_ffmpeg_settings()

        # FFmpeg command to capture X11 display + PulseAudio
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output file

            # Video input (X11 screen capture)
            "-f", "x11grab",
            "-framerate", settings["framerate"],
            "-video_size", settings["resolution"],
            "-i", config.DISPLAY,

            # Audio input (PulseAudio virtual sink monitor)
            "-f", "pulse",
            "-i", "virtual_speaker.monitor",

            # Video codec settings
            "-c:v", "libx264",
            "-preset", "veryfast",  # Faster encoding, good trade-off for size/cpu
            "-tune", "zerolatency",  # Low latency
            "-b:v", settings["video_bitrate"],
            "-pix_fmt", "yuv420p",

            # Audio codec settings
            "-c:a", "aac",
            "-b:a", settings["audio_bitrate"],
            "-ar", "44100",  # Sample rate

            # Output format options
            # movflags: Write moov atom at the start (faststart) and allow fragmented mp4
            # This makes the file recoverable even if FFmpeg terminates abruptly
            "-movflags", "+faststart+frag_keyframe+empty_moov",

            # Output
            "-f", "mp4",
            str(output_path)
        ]

        return cmd
    
    async def start(self) -> Path:
        """Start recording"""
        if self.is_recording:
            logger.warning("Recording already in progress")
            return self.recording_path
        
        self.recording_path = self._get_output_path()
        
        # Ensure directory exists
        self.recording_path.parent.mkdir(parents=True, exist_ok=True)
        
        cmd = self._build_ffmpeg_command(self.recording_path)
        logger.info(f"Starting FFmpeg recording: {' '.join(cmd)}")
        
        try:
            # Use preexec_fn to ignore SIGINT in the FFmpeg process
            # This is more reliable than start_new_session in Docker containers
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE,  # Need stdin to send 'q' command
                start_new_session=True,  # Isolate FFmpeg from parent's signal group
            )

            self.is_recording = True
            self.start_time = datetime.now()

            # Wait a moment and check if FFmpeg is still running
            await asyncio.sleep(1)
            if self.process.returncode is not None:
                # FFmpeg failed to start, get error output
                stderr = await self.process.stderr.read()
                stderr_str = stderr.decode('utf-8', errors='ignore')
                logger.error(f"FFmpeg failed to start (exit code {self.process.returncode}): {stderr_str[:500]}")
                self.is_recording = False
                raise RuntimeError(f"FFmpeg failed to start: {stderr_str[:200]}")

            # Start a task to monitor FFmpeg stderr for errors
            self._stderr_task = asyncio.create_task(self._monitor_ffmpeg_stderr())

            logger.info(f"Recording started successfully: {self.recording_path}")
            return self.recording_path

        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            raise

    async def _monitor_ffmpeg_stderr(self):
        """Monitor FFmpeg stderr for errors and log them"""
        if not self.process or not self.process.stderr:
            return
        try:
            while True:
                line = await self.process.stderr.readline()
                if not line:
                    break
                line_str = line.decode('utf-8', errors='ignore').strip()
                if line_str:
                    # Only log errors and important messages
                    if 'error' in line_str.lower() or 'failed' in line_str.lower():
                        logger.error(f"[FFmpeg] {line_str}")
                    elif 'warning' in line_str.lower():
                        logger.warning(f"[FFmpeg] {line_str}")
        except Exception as e:
            logger.debug(f"FFmpeg stderr monitor ended: {e}")
    
    async def stop(self) -> Optional[Path]:
        """Stop recording gracefully"""
        # Log recording directory contents for debugging
        try:
            recording_dir = Path(config.RECORDING_DIR)
            if recording_dir.exists():
                files = list(recording_dir.glob("*.mp4"))
                logger.info(f"Recording directory contents: {[f.name for f in files]}")
        except Exception as e:
            logger.debug(f"Could not list recording directory: {e}")

        if not self.is_recording or not self.process:
            logger.warning("No recording in progress")
            # Still check if file exists (process might have been killed externally)
            if self.recording_path and self.recording_path.exists():
                size = self.recording_path.stat().st_size
                if size > 0:
                    logger.info(f"Recording file found despite no active process: {self.recording_path} ({size / 1024 / 1024:.2f} MB)")
                    return self.recording_path
            return None

        logger.info("Stopping recording...")

        process_alive = self.process.returncode is None

        try:
            # Cancel stderr monitor task
            if hasattr(self, '_stderr_task') and self._stderr_task:
                self._stderr_task.cancel()
                try:
                    await self._stderr_task
                except asyncio.CancelledError:
                    pass

            if process_alive:
                # Method 1: Send 'q' via stdin (FFmpeg's graceful quit command)
                try:
                    logger.info("Sending 'q' to FFmpeg for graceful stop...")
                    self.process.stdin.write(b'q')
                    await self.process.stdin.drain()
                except Exception as e:
                    logger.warning(f"Could not send 'q' to FFmpeg: {e}")
                    # Method 2: Try SIGTERM (more graceful than SIGINT)
                    try:
                        logger.info("Sending SIGTERM to FFmpeg...")
                        self.process.send_signal(signal.SIGTERM)
                    except ProcessLookupError:
                        logger.warning("FFmpeg process already terminated")

                # Wait for process to finish
                try:
                    await asyncio.wait_for(self.process.wait(), timeout=10)
                    logger.info(f"FFmpeg exited with code: {self.process.returncode}")
                except asyncio.TimeoutError:
                    logger.warning("FFmpeg didn't stop gracefully, killing...")
                    try:
                        self.process.kill()
                        await self.process.wait()
                    except ProcessLookupError:
                        pass  # Already dead
            else:
                logger.warning(f"FFmpeg process already terminated with code: {self.process.returncode}")

            self.is_recording = False

            # Get duration
            if self.start_time:
                duration = (datetime.now() - self.start_time).total_seconds()
                logger.info(f"Recording stopped. Duration: {duration:.1f}s")

            # Wait a moment for file system to sync
            await asyncio.sleep(0.5)

            # Verify file exists and has content
            if self.recording_path:
                logger.info(f"Checking for recording at: {self.recording_path}")
                if self.recording_path.exists():
                    size = self.recording_path.stat().st_size
                    if size > 0:
                        logger.info(f"Recording saved: {self.recording_path} ({size / 1024 / 1024:.2f} MB)")
                        return self.recording_path
                    else:
                        logger.warning(f"Recording file is empty: {self.recording_path}")
                else:
                    logger.error(f"Recording file not found at: {self.recording_path}")
                    # Try to find any recording file in the directory
                    recording_dir = Path(config.RECORDING_DIR)
                    if recording_dir.exists():
                        mp4_files = sorted(recording_dir.glob("*.mp4"), key=lambda f: f.stat().st_mtime, reverse=True)
                        if mp4_files:
                            latest = mp4_files[0]
                            size = latest.stat().st_size
                            if size > 0:
                                logger.info(f"Found alternative recording: {latest} ({size / 1024 / 1024:.2f} MB)")
                                return latest
            return None

        except Exception as e:
            logger.error(f"Error stopping recording: {e}")
            # Still try to return the file if it exists
            if self.recording_path and self.recording_path.exists():
                size = self.recording_path.stat().st_size
                if size > 0:
                    logger.info(f"Recording file recovered after error: {self.recording_path} ({size / 1024 / 1024:.2f} MB)")
                    self.is_recording = False
                    return self.recording_path
            raise
    
    def get_duration_seconds(self) -> int:
        """Get current recording duration in seconds"""
        if not self.start_time:
            return 0
        return int((datetime.now() - self.start_time).total_seconds())
    
    async def is_max_duration_reached(self) -> bool:
        """Check if max duration has been reached"""
        max_seconds = config.MAX_DURATION_HOURS * 3600
        return self.get_duration_seconds() >= max_seconds
