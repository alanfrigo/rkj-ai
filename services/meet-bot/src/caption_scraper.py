"""
Meet Bot - Caption Scraper
Captures live captions from Google Meet with speaker names.
Based on approach from: https://www.recall.ai/blog/how-i-built-an-in-house-google-meet-bot

Google Meet captions include the speaker name, so we can get reliable
speaker attribution by scraping the captions in real-time.
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional, List, Callable
from dataclasses import dataclass, field

from playwright.async_api import Page

logger = logging.getLogger(__name__)


@dataclass
class CaptionSegment:
    """A segment of text spoken by a single speaker"""
    speaker: str
    text: str
    start_ms: int
    end_ms: int
    
    def to_dict(self) -> dict:
        return {
            "speaker": self.speaker,
            "text": self.text,
            "start_ms": self.start_ms,
            "end_ms": self.end_ms
        }


class CaptionScraper:
    """
    Scrapes live captions from Google Meet.
    
    Google Meet renders captions in a live-updating region element.
    The captions include the speaker's name, which we extract using
    MutationObserver.
    """
    
    def __init__(self, page: Page):
        self.page = page
        self.segments: List[CaptionSegment] = []
        self.is_scraping = False
        self.start_time: Optional[datetime] = None
        self._active_segments: dict = {}  # speaker -> current segment
    
    # JavaScript to inject MutationObserver for caption scraping
    CAPTION_SCRAPE_JS = """
    () => {
        // Selectors for speaker name badge in captions
        const SPEAKER_BADGE_SELECTORS = '.NWpY1d, .xoMHSc, [data-self-name]';
        
        // Elements/text patterns to ignore (UI elements, icons, button labels)
        const IGNORE_PATTERNS = [
            'more_vert', 'more_horiz', 'keyboard_arrow', 'arrow_drop',
            'videocam', 'mic', 'present', 'share', 'close', 'check',
            'remove_circle', 'add_circle', 'person_add', 'group_add',
            'settings', 'help', 'info', 'warning', 'error',
            'Ativar', 'Desativar', 'Voltar', 'Sair', 'Entrar',
            'feedback', 'Enviar', 'Cancelar', 'OK', 'Fechar',
            'tela inicial', 'home screen', 'Saiba mais', 'Learn more',
            'opções para', 'options for', 'Não é possível',
            'ctrl +', 'Ctrl+', 'shift +', 'Shift+',
            'remover', 'remove', 'adicionar', 'add'
        ];
        
        let lastSpeaker = 'Unknown';
        let captionCount = 0;
        let lastCaptionText = '';
        
        // Check if text is likely a real caption (not UI element)
        const isRealCaption = (text) => {
            if (!text || text.length < 3) return false;
            const lower = text.toLowerCase();
            
            // Check against ignore patterns
            for (const pattern of IGNORE_PATTERNS) {
                if (lower.includes(pattern.toLowerCase())) return false;
            }
            
            // Icon text patterns (Material Icons)
            if (/^[a-z_]+$/.test(text) && text.includes('_')) return false;
            
            // Very short text that's probably UI
            if (text.length < 5 && !/[aeioué]/.test(lower)) return false;
            
            return true;
        };
        
        // Extract speaker name from caption node
        const getSpeaker = (node) => {
            const badge = node.querySelector(SPEAKER_BADGE_SELECTORS);
            const speaker = badge?.textContent?.trim();
            if (speaker && speaker.length > 1 && speaker.length < 60 && isRealCaption(speaker)) {
                return speaker;
            }
            return lastSpeaker;
        };
        
        // Extract caption text (without speaker name)
        const getText = (node) => {
            const clone = node.cloneNode(true);
            // Remove speaker badge from clone
            clone.querySelectorAll(SPEAKER_BADGE_SELECTORS).forEach(el => el.remove());
            // Remove any icon elements
            clone.querySelectorAll('[class*="icon"], [class*="material"]').forEach(el => el.remove());
            return clone.textContent?.trim() ?? '';
        };
        
        // Send caption to exposed callback
        const sendCaption = (node) => {
            const text = getText(node);
            const speaker = getSpeaker(node);
            
            // Only process if it's a real caption
            if (text && isRealCaption(text) && text !== lastCaptionText) {
                // Don't process if text is same as speaker name
                if (text.toLowerCase() === speaker.toLowerCase()) return;
                
                captionCount++;
                console.log(`[Caption ${captionCount}] ${speaker}: ${text}`);
                
                if (window.onCaptionReceived) {
                    window.onCaptionReceived(speaker, text, Date.now());
                }
                lastSpeaker = speaker;
                lastCaptionText = text;
            }
        };
        
        // Find the captions container (aria-live region)
        const findCaptionContainer = () => {
            // Google Meet captions are typically in an aria-live region
            const liveRegions = document.querySelectorAll('[aria-live="polite"], [role="region"]');
            for (const region of liveRegions) {
                // Caption container is usually relatively small and positioned at bottom
                const rect = region.getBoundingClientRect();
                if (rect.bottom > window.innerHeight * 0.7 && rect.height < 200) {
                    return region;
                }
            }
            // Fallback to any aria-live region
            return document.querySelector('[aria-live="polite"]') || document.body;
        };
        
        const captionContainer = findCaptionContainer();
        console.log('[CaptionScraper] Caption container:', captionContainer.tagName, captionContainer.className);
        
        // Watch for caption changes only in the caption container
        const observer = new MutationObserver((mutations) => {
            for (const m of mutations) {
                // New caption elements added
                for (const node of m.addedNodes) {
                    if (node instanceof HTMLElement) {
                        sendCaption(node);
                    }
                }
                
                // Text changes within existing caption elements
                if (m.type === 'characterData' && m.target?.parentElement instanceof HTMLElement) {
                    sendCaption(m.target.parentElement);
                }
            }
        });
        
        // Start observing
        observer.observe(captionContainer, {
            childList: true,
            characterData: true,
            subtree: true
        });
        
        console.log('[CaptionScraper] MutationObserver installed on caption container');
        return { success: true, message: 'Caption scraping started' };
    }
    """
    
    ENABLE_CAPTIONS_JS = """
    async () => {
        // Try to enable captions via keyboard shortcut first
        const result = { enabled: false, method: null };
        
        // Method 1: Press 'c' key (Google Meet shortcut for captions)
        document.dispatchEvent(new KeyboardEvent('keydown', { 
            key: 'c', 
            code: 'KeyC', 
            keyCode: 67,
            bubbles: true 
        }));
        
        await new Promise(r => setTimeout(r, 1000));
        
        // Check if captions region appeared
        const captionRegion = document.querySelector('[aria-live="polite"]');
        if (captionRegion) {
            result.enabled = true;
            result.method = 'keyboard-c';
            return result;
        }
        
        // Method 2: Try to find and click captions button
        const captionButtons = [
            '[aria-label*="caption" i]',
            '[aria-label*="legenda" i]',
            '[aria-label*="subtitle" i]',
            'button[data-tooltip*="caption" i]',
            'button[data-tooltip*="legenda" i]'
        ];
        
        for (const selector of captionButtons) {
            const btn = document.querySelector(selector);
            if (btn) {
                btn.click();
                await new Promise(r => setTimeout(r, 1000));
                result.enabled = true;
                result.method = 'button-click';
                return result;
            }
        }
        
        // Method 3: Try Shift+C
        document.dispatchEvent(new KeyboardEvent('keydown', { 
            key: 'C', 
            code: 'KeyC', 
            shiftKey: true,
            bubbles: true 
        }));
        
        await new Promise(r => setTimeout(r, 1000));
        
        const captionRegion2 = document.querySelector('[aria-live="polite"]');
        if (captionRegion2) {
            result.enabled = true;
            result.method = 'keyboard-shift-c';
        }
        
        return result;
    }
    """
    
    async def enable_captions(self) -> bool:
        """Try to enable captions in Google Meet"""
        logger.info("Attempting to enable captions...")
        
        try:
            # Wait a bit for the meeting to fully load
            await asyncio.sleep(2)
            
            # Try pressing 'c' to toggle captions
            await self.page.keyboard.press('c')
            await asyncio.sleep(1)
            
            # Check if captions region appeared
            caption_region = await self.page.query_selector('[aria-live="polite"]')
            if caption_region:
                logger.info("Captions enabled via 'c' key")
                return True
            
            # Try clicking captions button
            caption_selectors = [
                '[aria-label*="caption" i]',
                '[aria-label*="legenda" i]',
                '[aria-label*="Ativar legendas"]',
                '[aria-label*="Turn on captions"]',
            ]
            
            for selector in caption_selectors:
                try:
                    btn = await self.page.wait_for_selector(selector, timeout=2000)
                    if btn:
                        await btn.click()
                        logger.info(f"Captions enabled via button: {selector}")
                        await asyncio.sleep(1)
                        return True
                except:
                    pass
            
            logger.warning("Could not enable captions - will continue without")
            return False
            
        except Exception as e:
            logger.error(f"Error enabling captions: {e}")
            return False
    
    async def start_scraping(self, on_caption: Callable = None):
        """Start scraping captions"""
        logger.info("Starting caption scraping...")
        self.is_scraping = True
        self.start_time = datetime.now()
        self.segments = []
        self._active_segments = {}
        
        # Expose callback function to receive captions from browser
        async def handle_caption(speaker: str, text: str, timestamp_ms: int):
            """Handle caption received from browser"""
            elapsed_ms = int((datetime.now() - self.start_time).total_seconds() * 1000)
            
            # Filter out bot's own captions
            if 'Bot' in speaker or 'Meeting-Assistant' in speaker:
                return
            
            logger.info(f"[Caption] {speaker}: {text}")
            
            # Check if this extends an existing segment from same speaker
            if speaker in self._active_segments:
                active = self._active_segments[speaker]
                # If text is growing, update the segment
                if text.startswith(active.text) or len(text) > len(active.text):
                    active.text = text
                    active.end_ms = elapsed_ms
                else:
                    # New segment from same speaker
                    self.segments.append(active)
                    self._active_segments[speaker] = CaptionSegment(
                        speaker=speaker,
                        text=text,
                        start_ms=elapsed_ms,
                        end_ms=elapsed_ms + 1000
                    )
            else:
                # New speaker
                self._active_segments[speaker] = CaptionSegment(
                    speaker=speaker,
                    text=text,
                    start_ms=elapsed_ms,
                    end_ms=elapsed_ms + 1000
                )
            
            if on_caption:
                on_caption(speaker, text, elapsed_ms)
        
        # Expose the callback to the browser
        await self.page.expose_function('onCaptionReceived', handle_caption)
        
        # Inject the caption scraping script
        result = await self.page.evaluate(self.CAPTION_SCRAPE_JS)
        logger.info(f"Caption scraping initialized: {result}")
    
    async def stop_scraping(self) -> List[CaptionSegment]:
        """Stop scraping and return all captured segments"""
        logger.info("Stopping caption scraping...")
        self.is_scraping = False
        
        # Flush any active segments
        for speaker, segment in self._active_segments.items():
            self.segments.append(segment)
        
        self._active_segments = {}
        
        logger.info(f"Caption scraping complete: {len(self.segments)} segments captured")
        return self.segments
    
    def get_segments(self) -> List[CaptionSegment]:
        """Get all captured segments (including active ones)"""
        all_segments = list(self.segments)
        for segment in self._active_segments.values():
            all_segments.append(segment)
        return all_segments
