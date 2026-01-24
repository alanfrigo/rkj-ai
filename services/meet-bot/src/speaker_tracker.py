"""
Meet Bot - Speaker Tracker
Monitors Google Meet UI to detect active speakers during recording
"""
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from playwright.async_api import Page

logger = logging.getLogger(__name__)


class SpeakerEvent:
    """Represents a speaker change event"""
    def __init__(self, timestamp_ms: int, speaker_name: str, participants: List[str] = None):
        self.timestamp_ms = timestamp_ms
        self.speaker_name = speaker_name
        self.participants = participants or []
    
    def to_dict(self) -> dict:
        return {
            "timestamp_ms": self.timestamp_ms,
            "speaker_name": self.speaker_name,
            "participants": self.participants
        }


class SpeakerTracker:
    """
    Tracks active speakers during a Google Meet session.
    
    Uses DOM monitoring to detect:
    - Who is currently speaking (via visual indicators)
    - All participant names
    """
    
    def __init__(self, page: Page):
        self.page = page
        self.events: List[SpeakerEvent] = []
        self.participants: List[str] = []
        self.is_tracking = False
        self._tracking_task: Optional[asyncio.Task] = None
        self.start_time: Optional[datetime] = None
        self.polling_interval_ms = 1000  # Poll every 1 second
    
    # JavaScript function to detect active speaker in Google Meet
    # Conservative approach: only detect when we have strong evidence, never guess
    DETECT_SPEAKER_JS = """
    () => {
        const result = {
            activeSpeaker: null,
            participants: [],
            debugInfo: {}
        };
        
        try {
            // Get all participant tiles
            const tiles = document.querySelectorAll('[data-participant-id]');
            result.debugInfo.tileCount = tiles.length;
            
            // Collect participant names - ONLY from reliable sources
            const names = new Set();
            
            // Exclusion list - things that are NOT participant names
            const excludedPatterns = [
                'Bot', 'Meeting-Assistant', 'Você', 'You', 
                'Ativar', 'Desativar', 'Mute', 'Unmute',
                'camera', 'câmera', 'microphone', 'microfone',
                'apresent', 'present', 'compart', 'share'
            ];
            
            const isValidName = (name) => {
                if (!name || name.length < 3 || name.length > 60) return false;
                if (/^[0-9:]+$/.test(name)) return false; // Timestamps
                for (const pattern of excludedPatterns) {
                    if (name.toLowerCase().includes(pattern.toLowerCase())) return false;
                }
                return true;
            };
            
            for (const tile of tiles) {
                // PRIMARY SOURCE: data-self-name attribute - most reliable
                const selfName = tile.getAttribute('data-self-name');
                if (selfName && isValidName(selfName)) {
                    names.add(selfName);
                }
            }
            
            result.participants = [...names];
            result.debugInfo.participantCount = names.size;
            
            // SPEAKER DETECTION - Only when we have real evidence
            // DO NOT use fallback - it's better to have no speaker than wrong speaker
            
            // Strategy 1: Look for data-is-speaking attribute (if Google uses it)
            const speakingElements = document.querySelectorAll('[data-is-speaking="true"]');
            for (const el of speakingElements) {
                const tile = el.closest('[data-participant-id]');
                if (tile) {
                    const name = tile.getAttribute('data-self-name');
                    if (name && isValidName(name)) {
                        result.activeSpeaker = name;
                        result.debugInfo.detectionMethod = 'data-is-speaking';
                        break;
                    }
                }
            }
            
            // Strategy 2: Check for speaking indicator in aria-label
            if (!result.activeSpeaker) {
                const speakingIndicators = document.querySelectorAll(
                    '[aria-label*="está falando"], [aria-label*="is speaking"], ' +
                    '[aria-label*="is talking"], [aria-label*="está a falar"]'
                );
                for (const indicator of speakingIndicators) {
                    const tile = indicator.closest('[data-participant-id]');
                    if (tile) {
                        const name = tile.getAttribute('data-self-name');
                        if (name && isValidName(name)) {
                            result.activeSpeaker = name;
                            result.debugInfo.detectionMethod = 'aria-speaking';
                            break;
                        }
                    }
                }
            }
            
            // Strategy 3: Large tile in speaker view (only if SINGLE large tile)
            if (!result.activeSpeaker) {
                const largeTiles = [...tiles].filter(tile => {
                    const rect = tile.getBoundingClientRect();
                    return rect.width > 800 && rect.height > 500;
                });
                
                if (largeTiles.length === 1) {
                    const name = largeTiles[0].getAttribute('data-self-name');
                    if (name && isValidName(name)) {
                        result.activeSpeaker = name;
                        result.debugInfo.detectionMethod = 'speaker-view';
                    }
                }
            }
            
            // NO FALLBACK - if we can't detect who's speaking, leave it null
            // It's better to have no speaker than wrong speaker
            
        } catch (e) {
            result.debugInfo.error = e.message;
        }
        
        return result;
    }
    """
    
    async def start_tracking(self):
        """Start tracking speakers"""
        if self.is_tracking:
            logger.warning("Speaker tracking already running")
            return
        
        logger.info("Starting speaker tracking...")
        self.is_tracking = True
        self.start_time = datetime.now()
        self.events = []
        
        # Start background polling task
        self._tracking_task = asyncio.create_task(self._tracking_loop())
    
    async def _tracking_loop(self):
        """Background loop that polls for active speaker"""
        last_speaker = None
        
        while self.is_tracking:
            try:
                # Get current elapsed time
                elapsed_ms = int((datetime.now() - self.start_time).total_seconds() * 1000)
                
                # Detect active speaker via JavaScript
                result = await self.page.evaluate(self.DETECT_SPEAKER_JS)
                
                active_speaker = result.get("activeSpeaker")
                participants = result.get("participants", [])
                debug_info = result.get("debugInfo", {})
                
                # Update participant list
                if participants:
                    self.participants = list(set(self.participants + participants))
                
                # Log speaker change
                if active_speaker and active_speaker != last_speaker:
                    logger.info(f"[Speaker] {active_speaker} started speaking at {elapsed_ms}ms")
                    event = SpeakerEvent(elapsed_ms, active_speaker, participants)
                    self.events.append(event)
                    last_speaker = active_speaker
                
                # Debug logging (less frequent)
                if len(self.events) % 10 == 1:
                    logger.debug(f"Speaker tracking: {len(self.events)} events, {len(self.participants)} participants, method: {debug_info.get('detectionMethod', 'none')}")
                
            except Exception as e:
                logger.debug(f"Speaker detection error: {e}")
            
            # Wait for next poll
            await asyncio.sleep(self.polling_interval_ms / 1000)
    
    async def stop_tracking(self) -> List[SpeakerEvent]:
        """Stop tracking and return events"""
        logger.info("Stopping speaker tracking...")
        self.is_tracking = False
        
        if self._tracking_task:
            self._tracking_task.cancel()
            try:
                await self._tracking_task
            except asyncio.CancelledError:
                pass
        
        logger.info(f"Speaker tracking complete: {len(self.events)} events, {len(self.participants)} participants")
        return self.events
    
    def get_participants(self) -> List[str]:
        """Get list of all participants detected"""
        return self.participants
    
    def get_speaker_at_time(self, timestamp_ms: int) -> Optional[str]:
        """Get the speaker who was active at a given timestamp"""
        speaker = None
        for event in self.events:
            if event.timestamp_ms <= timestamp_ms:
                speaker = event.speaker_name
            else:
                break
        return speaker
    
    def save_events(self, output_path: Path) -> Path:
        """Save speaker events to JSON file"""
        data = {
            "participants": self.participants,
            "events": [e.to_dict() for e in self.events],
            "recorded_at": self.start_time.isoformat() if self.start_time else None
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Speaker events saved: {output_path}")
        return output_path
    
    @classmethod
    def load_events(cls, input_path: Path) -> tuple[List[str], List[SpeakerEvent]]:
        """Load speaker events from JSON file"""
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        participants = data.get("participants", [])
        events = [
            SpeakerEvent(e["timestamp_ms"], e["speaker_name"], e.get("participants", []))
            for e in data.get("events", [])
        ]
        
        return participants, events
