"""
Meet Bot - Google Meet Bot
Main bot class using Playwright to join and record meetings
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional

from playwright.async_api import async_playwright, Browser, Page, BrowserContext

from .config import config
from .recorder import Recorder
from .upload import R2Uploader
from .caption_scraper import CaptionScraper

logger = logging.getLogger(__name__)


class MeetBot:
    """
    Google Meet Bot using Playwright
    
    Handles:
    - Joining a Google Meet meeting
    - Recording screen and audio
    - Detecting when meeting ends
    - Uploading recording to R2
    """
    
    def __init__(self, meeting_id: str, meeting_url: str, user_id: str):
        self.meeting_id = meeting_id
        self.meeting_url = meeting_url
        self.user_id = user_id
        
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        self.recorder = Recorder(meeting_id)
        self.uploader = R2Uploader()
        self.caption_scraper: Optional[CaptionScraper] = None
        
        self.is_in_meeting = False
        self.meeting_ended = False
        self.start_time: Optional[datetime] = None
    
    async def start(self):
        """Initialize Playwright and browser with stealth mode"""
        logger.info("Starting Playwright browser with stealth mode...")
        
        self.playwright = await async_playwright().start()
        
        # Launch Chromium with stealth settings
        self.browser = await self.playwright.chromium.launch(
            headless=False,  # Need headed mode for proper rendering
            args=[
                "--kiosk", # Remove browser UI (full screen, no address bar)
                "--disable-infobars",
                "--use-fake-ui-for-media-stream",  # Auto-allow camera/mic
                "--use-fake-device-for-media-stream",
                "--use-file-for-fake-video-capture=/assets/camera_loop.y4m", # Custom camera video (must be y4m/mjpeg)
                "--disable-blink-features=AutomationControlled",  # Hide automation
                "--disable-features=IsolateOrigins,site-per-process",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-background-networking",
                "--disable-extensions",
                "--disable-sync",
                "--disable-default-apps",
                "--no-first-run",
                "--no-default-browser-check",
                f"--window-size={config.RESOLUTION[0]},{config.RESOLUTION[1]}",
            ]
        )
        
        # Create context with realistic settings
        self.context = await self.browser.new_context(
            viewport={"width": config.RESOLUTION[0], "height": config.RESOLUTION[1]},
            permissions=["camera", "microphone"],
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            locale="pt-BR",
            timezone_id="America/Sao_Paulo",
            color_scheme="light",
            extra_http_headers={
                "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
            }
        )
        
        # Start immediately, no new_page needed as --app opens one, but we attach to it
        pages = self.context.pages
        if pages:
            self.page = pages[0]
        else:
            self.page = await self.context.new_page()

        # Add browser console and error listeners for debugging
        self.page.on("console", lambda msg: logger.debug(f"[Browser Console] {msg.type}: {msg.text}"))
        self.page.on("pageerror", lambda exc: logger.error(f"[Browser Page Error] {exc}"))

        logger.info("Browser ready with stealth and kiosk mode")
    
    async def _apply_stealth_scripts(self):
        """Apply comprehensive stealth scripts to hide automation detection"""
        
        # Comprehensive stealth script based on playwright-extra-stealth
        stealth_js = """
        (function() {
            // === 1. NAVIGATOR WEBDRIVER ===
            // Delete the property instead of redefining
            delete Object.getPrototypeOf(navigator).webdriver;
            
            // Also handle the getter approach
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
                configurable: true
            });
            
            // === 2. CHROME RUNTIME ===
            window.chrome = {
                runtime: {
                    connect: function() {},
                    sendMessage: function() {},
                    id: undefined
                },
                loadTimes: function() {
                    return {
                        commitLoadTime: Date.now() / 1000 - 0.5,
                        connectionInfo: "http/1.1",
                        finishDocumentLoadTime: Date.now() / 1000 - 0.1,
                        finishLoadTime: Date.now() / 1000,
                        firstPaintAfterLoadTime: 0,
                        firstPaintTime: Date.now() / 1000 - 0.4,
                        navigationType: "Other",
                        npnNegotiatedProtocol: "unknown",
                        requestTime: Date.now() / 1000 - 0.6,
                        startLoadTime: Date.now() / 1000 - 0.5,
                        wasAlternateProtocolAvailable: false,
                        wasFetchedViaSpdy: false,
                        wasNpnNegotiated: false
                    };
                },
                csi: function() {
                    return {
                        onloadT: Date.now(),
                        pageT: Date.now() - performance.timing.navigationStart,
                        startE: performance.timing.navigationStart,
                        tran: 15
                    };
                },
                app: {
                    isInstalled: false,
                    InstallState: {DISABLED: "disabled", INSTALLED: "installed", NOT_INSTALLED: "not_installed"},
                    RunningState: {CANNOT_RUN: "cannot_run", READY_TO_RUN: "ready_to_run", RUNNING: "running"}
                }
            };
            
            // === 3. PLUGINS AND MIMETYPES ===
            const pluginData = [
                {name: "Chrome PDF Plugin", filename: "internal-pdf-viewer", description: "Portable Document Format"},
                {name: "Chrome PDF Viewer", filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai", description: ""},
                {name: "Native Client", filename: "internal-nacl-plugin", description: ""}
            ];
            
            const pluginArray = pluginData.map(p => {
                const plugin = Object.create(Plugin.prototype);
                Object.defineProperty(plugin, 'name', {value: p.name});
                Object.defineProperty(plugin, 'filename', {value: p.filename});
                Object.defineProperty(plugin, 'description', {value: p.description});
                Object.defineProperty(plugin, 'length', {value: 1});
                return plugin;
            });
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    const arr = [...pluginArray];
                    arr.item = i => arr[i];
                    arr.namedItem = n => arr.find(p => p.name === n);
                    arr.refresh = () => {};
                    return arr;
                }
            });
            
            // === 4. LANGUAGES ===
            Object.defineProperty(navigator, 'languages', {
                get: () => ['pt-BR', 'pt', 'en-US', 'en']
            });
            
            Object.defineProperty(navigator, 'language', {
                get: () => 'pt-BR'
            });
            
            // === 5. PERMISSIONS ===
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => {
                if (parameters.name === 'notifications') {
                    return Promise.resolve({state: Notification.permission});
                }
                return originalQuery.call(navigator.permissions, parameters);
            };
            
            // === 6. WEBGL VENDOR/RENDERER ===
            const getParameterProto = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) return 'Google Inc. (Intel)';
                if (parameter === 37446) return 'ANGLE (Intel, Intel(R) UHD Graphics 620, OpenGL 4.1)';
                return getParameterProto.call(this, parameter);
            };
            
            const getParameterProto2 = WebGL2RenderingContext.prototype.getParameter;
            WebGL2RenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) return 'Google Inc. (Intel)';
                if (parameter === 37446) return 'ANGLE (Intel, Intel(R) UHD Graphics 620, OpenGL 4.1)';
                return getParameterProto2.call(this, parameter);
            };
            
            // === 7. HARDWARE CONCURRENCY ===
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 8
            });
            
            // === 8. DEVICE MEMORY ===
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => 8
            });
            
            // === 9. PLATFORM ===
            Object.defineProperty(navigator, 'platform', {
                get: () => 'Win32'
            });
            
            // === 10. USER AGENT DATA ===
            Object.defineProperty(navigator, 'userAgentData', {
                get: () => ({
                    brands: [
                        {brand: "Not_A Brand", version: "8"},
                        {brand: "Chromium", version: "120"},
                        {brand: "Google Chrome", version: "120"}
                    ],
                    mobile: false,
                    platform: "Windows"
                })
            });
            
            // === 11. IFRAME CONTENT WINDOW ===
            // This is critical for Google detection
            const originalContentWindow = Object.getOwnPropertyDescriptor(HTMLIFrameElement.prototype, 'contentWindow');
            Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
                get: function() {
                    const win = originalContentWindow.get.call(this);
                    if (win) {
                        try {
                            Object.defineProperty(win.navigator, 'webdriver', {
                                get: () => false
                            });
                        } catch(e) {}
                    }
                    return win;
                }
            });
            
            // === 12. NOTIFICATION PERMISSIONS ===
            if (!window.Notification) {
                window.Notification = {
                    permission: 'default',
                    requestPermission: () => Promise.resolve('default')
                };
            }
            
            // === 13. MEDIA DEVICES ===
            if (navigator.mediaDevices) {
                const originalEnumerateDevices = navigator.mediaDevices.enumerateDevices;
                navigator.mediaDevices.enumerateDevices = async function() {
                    const devices = await originalEnumerateDevices.call(this);
                    if (devices.length === 0) {
                        return [
                            {deviceId: 'default', kind: 'audioinput', label: 'Default - Microphone', groupId: 'default'},
                            {deviceId: 'default', kind: 'videoinput', label: 'Default - Camera', groupId: 'default'},
                            {deviceId: 'default', kind: 'audiooutput', label: 'Default - Speakers', groupId: 'default'}
                        ];
                    }
                    return devices;
                };
            }
            
            // === 14. CONSOLE DEBUG DETECTION ===
            // Prevent detection via console.debug
            const originalDebug = console.debug;
            console.debug = function() {
                const stack = new Error().stack;
                if (stack && stack.includes('google')) {
                    return;
                }
                return originalDebug.apply(this, arguments);
            };
            
            console.log('[Stealth] All evasions applied');
        })();
        """
        
        await self.page.add_init_script(stealth_js)
        logger.info("Advanced stealth scripts applied")

    async def _capture_diagnostic_info(self, prefix: str = "diagnostic"):
        """Capture diagnostic information for debugging"""
        try:
            timestamp = datetime.now().strftime("%H%M%S")
            base_path = f"/recordings/{prefix}_{timestamp}"

            # Screenshot
            await self.page.screenshot(path=f"{base_path}.png")
            logger.info(f"Saved diagnostic screenshot: {base_path}.png")

            # HTML content
            html_content = await self.page.content()
            with open(f"{base_path}.html", "w") as f:
                f.write(html_content)
            logger.info(f"Saved diagnostic HTML: {base_path}.html")

            # Page info
            info = {
                "url": self.page.url,
                "title": await self.page.title(),
                "timestamp": datetime.now().isoformat()
            }

            # Try to capture visible text
            try:
                visible_text = await self.page.evaluate("""
                    () => {
                        const walker = document.createTreeWalker(
                            document.body,
                            NodeFilter.SHOW_TEXT,
                            null,
                            false
                        );
                        const texts = [];
                        let node;
                        while (node = walker.nextNode()) {
                            const text = node.textContent.trim();
                            if (text && text.length > 2) {
                                texts.push(text);
                            }
                        }
                        return texts.slice(0, 100).join(' | ');
                    }
                """)
                info["visible_text"] = visible_text[:2000] if visible_text else ""
            except Exception as e:
                logger.debug(f"Could not capture visible text: {e}")

            with open(f"{base_path}_info.json", "w") as f:
                import json
                json.dump(info, f, indent=2)
            logger.info(f"Saved diagnostic info: {base_path}_info.json")

            return info
        except Exception as e:
            logger.warning(f"Failed to capture diagnostic info: {e}")
            return None



    async def _handle_onboarding_popups(self):
        """Dismiss onboarding popups that might block the UI"""
        logger.info("Checking for onboarding popups...")
        
        # Selectors for popup buttons to click
        popup_selectors = [
            'span:text("Entendi")',
            'span:text("Got it")',
            'span:text("Agora não")', # Notifications
            'span:text("Not now")',
            'span:text("Dismiss")',
            'button[aria-label="Close"]',
            'button[aria-label="Fechar"]',
        ]
        
        # Try to find and click any of these - use short timeouts for speed
        for _ in range(3): # Try a few times
            clicked = False
            for selector in popup_selectors:
                try:
                    # Use very short timeout to check quickly
                    btn = await self.page.wait_for_selector(selector, timeout=500)
                    if btn and await btn.is_visible():
                        logger.info(f"Dismissing popup: {selector}")
                        await btn.click()
                        await asyncio.sleep(0.3)
                        clicked = True
                except:
                    pass
            if not clicked:
                break


    async def join_meeting(self) -> bool:
        """Join the Google Meet meeting with retry logic"""
        logger.info(f"Joining meeting: {self.meeting_url}")

        for attempt in range(1, config.MAX_JOIN_RETRIES + 1):
            logger.info(f"Join attempt {attempt}/{config.MAX_JOIN_RETRIES}")

            try:
                result = await self._attempt_join_meeting(attempt)
                if result:
                    self.is_in_meeting = True
                    self.start_time = datetime.now()
                    logger.info("Successfully joined meeting!")
                    await self.page.screenshot(path="/recordings/06_in_meeting.png")
                    return True

                # If it's a permanent failure (access denied, login required), don't retry
                if result is False:
                    logger.warning(f"Attempt {attempt} failed with permanent error, not retrying")
                    return False

            except TimeoutError as e:
                logger.warning(f"Attempt {attempt} timed out: {e}")
                await self._capture_diagnostic_info(f"timeout_attempt_{attempt}")

            except Exception as e:
                logger.warning(f"Attempt {attempt} failed with error: {e}")
                await self._capture_diagnostic_info(f"error_attempt_{attempt}")

            # Calculate exponential backoff delay
            if attempt < config.MAX_JOIN_RETRIES:
                delay = min(
                    config.INITIAL_RETRY_DELAY * (2 ** (attempt - 1)),
                    config.MAX_RETRY_DELAY
                )
                logger.info(f"Waiting {delay}s before retry...")
                await asyncio.sleep(delay)

                # Reload page for fresh attempt
                logger.info("Reloading page for new attempt...")
                try:
                    await self.page.reload(timeout=config.PAGE_LOAD_TIMEOUT * 1000)
                    await asyncio.sleep(3)
                except Exception as reload_err:
                    logger.warning(f"Page reload failed, navigating to URL: {reload_err}")
                    await self.page.goto(self.meeting_url, timeout=config.PAGE_LOAD_TIMEOUT * 1000)
                    await asyncio.sleep(3)

        logger.error(f"Failed to join meeting after {config.MAX_JOIN_RETRIES} attempts")
        await self._capture_diagnostic_info("final_failure")
        return False

    async def _attempt_join_meeting(self, attempt: int) -> bool:
        """Single attempt to join the meeting. Returns True on success, False on permanent failure, raises on retryable error."""

        # Navigate to meeting URL only on first attempt
        if attempt == 1:
            logger.info("Navigating to meeting URL...")
            await self.page.goto(self.meeting_url, timeout=config.PAGE_LOAD_TIMEOUT * 1000)
            
            # fast wait for network idle to ensure basic load
            try:
                await self.page.wait_for_load_state("networkidle", timeout=5000)
            except:
                pass


        # Screenshot after page load
        await self.page.screenshot(path=f"/recordings/01_page_loaded_attempt_{attempt}.png")
        logger.info(f"Page URL after load: {self.page.url}")
        logger.info(f"Page title: {await self.page.title()}")

        # Dismiss any onboarding popups
        await self._handle_onboarding_popups()

        # Check for and handle generic errors (retryable)
        if await self._handle_generic_error_with_retry():
            # Error was found and handled, but we should re-check for more issues
            await asyncio.sleep(2)
            await self._handle_onboarding_popups()

        # Check for access denied (permanent failure)
        access_denied_selectors = [
            'text="Não é possível participar desta videochamada"',
            'text="You can\'t join this video call"',
            'text="Can\'t join this video call"',
            'text="Update your browser"',
            'text="Atualize seu navegador"',
            'text="You\'ve been denied access"',
            'text="Seu acesso foi negado"',
            'text="This meeting has ended"',
            'text="Esta reunião terminou"',
        ]

        for selector in access_denied_selectors:
            try:
                denied_elem = await self.page.query_selector(selector)
                if denied_elem:
                    logger.error(f"ACCESS DENIED: {selector}")
                    await self._capture_diagnostic_info("access_denied")
                    return False  # Permanent failure
            except:
                pass

        # Check if we need to sign in (permanent failure)
        signin_required_selectors = [
            'text="Sign in to join this meeting"',
            'text="Faça login para participar desta reunião"',
            'a[href*="accounts.google.com/signin"]'
        ]

        for selector in signin_required_selectors:
            try:
                signin = await self.page.query_selector(selector)
                if signin:
                    logger.error("Meeting requires login to join. Anonymous access not allowed.")
                    await self._capture_diagnostic_info("login_required")
                    return False  # Permanent failure
            except:
                pass

        # Handle initial prompts and join flow

        # 1. Wait for and set the display name
        logger.info("Looking for name input field...")
        try:
            name_input = await self.page.wait_for_selector(
                'input[aria-label="Your name"], input[placeholder*="name"], input[aria-label="Seu nome"], input[type="text"]',
                timeout=10000
            )
            if name_input:
                logger.info("Found name input field")
                await name_input.click()
                await name_input.fill(config.BOT_NAME)
                logger.info(f"Set bot name: {config.BOT_NAME}")
                await self.page.keyboard.press("Enter")
                await asyncio.sleep(1)
                await self.page.screenshot(path="/recordings/03_name_entered.png")
            else:
                logger.warning("Name input selector returned None")
        except Exception as e:
            logger.debug(f"No name input found (might be authenticated or different UI): {e}")

        # 2. Turn off camera and microphone
        await self._turn_off_camera_mic()
        await self.page.screenshot(path="/recordings/04_before_join_click.png")

        # 3. Check if we're already in waiting room or meeting (can happen after name entry)
        already_in_waiting_or_meeting = await self._check_already_in_waiting_or_meeting()

        if not already_in_waiting_or_meeting:
            # Click "Ask to join" or "Join now" button
            await self._click_join_button()
        else:
            logger.info("Already in waiting room or meeting, skipping join button click")

        # 4. Wait to be in the meeting
        await self._wait_for_meeting_join()

        return True

    async def _check_already_in_waiting_or_meeting(self) -> bool:
        """Check if we're already in waiting room or meeting (can happen after name entry with auto-join)"""
        # Check for waiting room indicators
        waiting_indicators = [
            'text="Aguarde até que um organizador da reunião adicione você à chamada"',
            'text="Wait until a meeting organizer adds you to the call"',
            'text="Waiting for someone to let you in"',
            'text="Aguardando alguém permitir sua entrada"',
        ]

        for indicator in waiting_indicators:
            try:
                elem = await self.page.query_selector(indicator)
                if elem:
                    logger.info(f"Already in waiting room: {indicator}")
                    return True
            except:
                pass

        # Check for meeting indicators (already admitted)
        meeting_indicators = [
            '[aria-label*="Sair da chamada"]',
            '[aria-label*="Leave call"]',
            '[data-participant-id]',
        ]

        for indicator in meeting_indicators:
            try:
                elem = await self.page.query_selector(indicator)
                if elem:
                    logger.info(f"Already in meeting: {indicator}")
                    return True
            except:
                pass

        return False

    async def _handle_generic_error_with_retry(self) -> bool:
        """Check for and handle generic errors that might be fixed with a reload. Returns True if error was found and handled."""
        generic_error_selectors = [
            'text="Não foi possível iniciar a videochamada devido a um erro"',
            'text="Unable to start video call due to an error"',
            'text="Tente novamente em alguns instantes"',
            'text="Try again in a few moments"',
            'text="Something went wrong"',
            'text="Algo deu errado"',
            'text="An error occurred"',
            'text="Ocorreu um erro"',
        ]

        for selector in generic_error_selectors:
            try:
                error_elem = await self.page.query_selector(selector)
                if error_elem:
                    logger.warning(f"Encountered generic error: {selector}")
                    await self._capture_diagnostic_info("generic_error_before_reload")

                    # Try clicking a retry button if available
                    retry_selectors = [
                        'button:has-text("Try again")',
                        'button:has-text("Tentar novamente")',
                        'button:has-text("Retry")',
                        'span:text("Try again")',
                        'span:text("Tentar novamente")',
                    ]
                    for retry_sel in retry_selectors:
                        try:
                            retry_btn = await self.page.query_selector(retry_sel)
                            if retry_btn and await retry_btn.is_visible():
                                logger.info(f"Clicking retry button: {retry_sel}")
                                await retry_btn.click()
                                await asyncio.sleep(3)
                                return True
                        except:
                            pass

                    # No retry button, reload the page
                    logger.info("No retry button found, reloading page...")
                    await self.page.reload()
                    await asyncio.sleep(5)
                    return True
            except:
                pass

        return False
    
    async def _turn_off_camera_mic(self):
        """Turn off camera and microphone before joining"""
        camera_off = False
        mic_off = False

        # Camera toggle selectors (EN + PT-BR)
        camera_selectors = [
            '[data-is-muted="false"][aria-label*="camera"]',
            '[aria-label*="Turn off camera"]',
            '[aria-label*="Desativar câmera"]',
            '[aria-label*="Desligar câmera"]',
            'button[aria-label*="camera"]',
            'button[aria-label*="câmera"]',
            '[data-tooltip*="camera"]',
            '[data-tooltip*="câmera"]',
        ]

        for selector in camera_selectors:
            # We want to keep camera ON for the robot emoji
             pass
             # try:
             #    camera_btn = await self.page.query_selector(selector)
             #    if camera_btn and await camera_btn.is_visible():
             #        await camera_btn.click()
             #        logger.info(f"Camera turned off via: {selector}")
             #        camera_off = True
             #        break
             # except:
             #    pass

        # Microphone toggle selectors (EN + PT-BR)
        mic_selectors = [
            '[data-is-muted="false"][aria-label*="microphone"]',
            '[aria-label*="Turn off microphone"]',
            '[aria-label*="Desativar microfone"]',
            '[aria-label*="Desligar microfone"]',
            'button[aria-label*="microphone"]',
            'button[aria-label*="microfone"]',
            '[data-tooltip*="microphone"]',
            '[data-tooltip*="microfone"]',
        ]

        for selector in mic_selectors:
            try:
                mic_btn = await self.page.query_selector(selector)
                if mic_btn and await mic_btn.is_visible():
                    await mic_btn.click()
                    logger.info(f"Microphone turned off via: {selector}")
                    mic_off = True
                    break
            except:
                pass

        # Fallback: use keyboard shortcuts
        # Google Meet shortcuts: Ctrl+D for camera, Ctrl+E for mic
        if not camera_off:
            pass
            # try:
            #     logger.info("Trying keyboard shortcut Ctrl+D for camera")
            #     await self.page.keyboard.press("Control+d")
            #     await asyncio.sleep(0.5)
            # except Exception as e:
            #     logger.debug(f"Keyboard shortcut for camera failed: {e}")

        if not mic_off:
            try:
                logger.info("Trying keyboard shortcut Ctrl+E for mic")
                await self.page.keyboard.press("Control+e")
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.debug(f"Keyboard shortcut for mic failed: {e}")
    
    async def _click_join_button(self):
        """Click the join button with multiple fallback strategies"""
        logger.info("Attempting to click join button...")

        # Strategy 1: Use get_by_role for more robust button detection
        role_based_buttons = [
            ("Ask to join", None),
            ("Pedir para participar", None),
            ("Join now", None),
            ("Participar agora", None),
            ("Join", None),
            ("Participar", None),
        ]

        for button_text, _ in role_based_buttons:
            try:
                btn = self.page.get_by_role("button", name=button_text)
                if await btn.count() > 0 and await btn.first.is_visible():
                    logger.info(f"Found join button via get_by_role: {button_text}")
                    await btn.first.click()
                    await asyncio.sleep(1)
                    await self.page.screenshot(path="/recordings/05_after_join_click.png")
                    logger.info(f"Clicked join button: {button_text}")
                    return
            except Exception:
                continue

        # Strategy 2: CSS selectors (extended for 2024/2025)
        join_selectors = [
            'button:has-text("Ask to join")',
            'button:has-text("Pedir para participar")',
            'button:has-text("Join now")',
            'button:has-text("Participar agora")',
            'button:has-text("Join")',
            'button:has-text("Participar")',
            'span:text("Ask to join")',
            'span:text("Pedir para participar")',
            'span:text("Join now")',
            'span:text("Participar agora")',
            '[jsname="Qx7uuf"]',
            # Data attributes
            '[data-mdc-dialog-action="join"]',
            'button[data-idom-class*="join"]',
        ]

        for selector in join_selectors:
            try:
                btn = await self.page.wait_for_selector(selector, timeout=2000)
                if btn and await btn.is_visible():
                    logger.info(f"Found join button: {selector}")
                    await btn.click()
                    await asyncio.sleep(1)
                    await self.page.screenshot(path="/recordings/05_after_join_click.png")
                    logger.info(f"Clicked join button: {selector}")
                    return
            except Exception:
                continue

        # Strategy 3: Fallback with Enter key (button might already be focused)
        logger.info("Trying Enter key as fallback for join button...")
        await self.page.keyboard.press("Enter")
        await asyncio.sleep(1)
        await self.page.screenshot(path="/recordings/05_after_enter_key.png")

        # Check if we're now joining
        joining_indicators = [
            'text="Joining"',
            'text="Entrando"',
            'text="Asking to join"',
            'text="Pedindo para participar"',
        ]
        for indicator in joining_indicators:
            try:
                elem = await self.page.query_selector(indicator)
                if elem:
                    logger.info(f"Enter key worked, detected: {indicator}")
                    return
            except:
                pass

        # Strategy 4: Tab + Enter (in case button needs to be focused first)
        logger.info("Trying Tab+Enter as fallback...")
        for _ in range(5):  # Try a few tabs
            await self.page.keyboard.press("Tab")
            await asyncio.sleep(0.2)
        await self.page.keyboard.press("Enter")
        await asyncio.sleep(1)
        await self.page.screenshot(path="/recordings/05_after_tab_enter.png")

        # Final fallback: dump page content if join button not found
        logger.warning("Could not find or click join button - check screenshots")
        await self._capture_diagnostic_info("no_join_button")
    
    async def _wait_for_meeting_join(self):
        """Wait until we're actually in the meeting (not just waiting room)"""

        # Indicators that we're IN the meeting (not waiting room) - 2024/2025 selectors
        # Using simpler attribute selectors for better reliability
        meeting_indicators = [
            # Participant tiles - MOST RELIABLE indicator of being in meeting
            '[data-participant-id]',
            '[data-requested-participant-id]',
            '[data-self-name]',

            # Leave call button (PT-BR and EN)
            '[aria-label="Sair da chamada"]',
            '[aria-label="Leave call"]',

            # Chat/Participants buttons (indicate we're in meeting)
            '[aria-label="Chat com todos"]',
            '[aria-label="Chat with everyone"]',
            '[aria-label*="Mostrar todos"]',
            '[aria-label*="Show everyone"]',

            # Meeting controls (mute state only exists in meeting)
            '[data-is-muted="true"]',
            '[data-is-muted="false"]',

            # Control labels
            '[aria-label="Controles de chamada"]',
            '[aria-label="Call controls"]',

            # "You're the only one here" message
            'text="Só você está aqui"',
            'text="You\'re the only one here"',
        ]

        # Indicators that we're in WAITING ROOM (need to keep waiting)
        waiting_room_indicators = [
            'text="Waiting for someone to let you in"',
            'text="Aguardando alguém permitir sua entrada"',
            'text="Someone will let you in soon"',
            'text="Alguém deixará você entrar em breve"',
            'text="Asking to be admitted"',
            'text="Pedindo para participar"',
            'text="Getting ready"',
            'text="Preparando"',
            'text="Waiting to be let in"',
            'text="Aguardando ser admitido"',
            # PT-BR variations for waiting room
            'text="Aguarde até que um organizador da reunião adicione você à chamada"',
            'text="Wait until a meeting organizer adds you to the call"',
            'text="Aguarde até que alguém permita sua entrada"',
        ]

        # Failure indicators (should raise immediately)
        failure_indicators = [
            'text="You\'ve been denied access"',
            'text="Seu acesso foi negado"',
            'text="This meeting has ended"',
            'text="Esta reunião terminou"',
            'text="Meeting has ended"',
            'text="A reunião terminou"',
            'text="You can\'t join this meeting"',
            'text="Você não pode participar desta reunião"',
        ]

        logger.info("Waiting to be admitted to meeting...")

        for i in range(config.JOIN_TIMEOUT):
            # First check for failure indicators
            for failure_sel in failure_indicators:
                try:
                    failure_elem = await self.page.query_selector(failure_sel)
                    if failure_elem:
                        logger.error(f"Join failed - detected: {failure_sel}")
                        await self._capture_diagnostic_info("join_failed")
                        raise Exception(f"Join failed: {failure_sel}")
                except Exception as e:
                    if "Join failed" in str(e):
                        raise
                    pass

            # First check if we're in waiting room
            in_waiting = False
            for wait_sel in waiting_room_indicators:
                try:
                    wait_elem = await self.page.query_selector(wait_sel)
                    if wait_elem:
                        in_waiting = True
                        if i == 0 or i % 10 == 0:
                            logger.info(f"In waiting room: {wait_sel}")
                        break
                except:
                    pass

            # If not in waiting room, check if we're in meeting
            if not in_waiting:
                # Check meeting indicators
                for selector in meeting_indicators:
                    try:
                        elem = await self.page.query_selector(selector)
                        if elem:
                            logger.info(f"Meeting joined - detected: {selector}")
                            return
                    except Exception as e:
                        if i == 0:  # Log errors only on first iteration
                            logger.debug(f"Selector failed {selector}: {e}")
                        pass

                # Extra debug: try to find ANY button with aria-label containing "Sair"
                if i == 0 or i % 10 == 0:
                    try:
                        # Use locator for more reliable detection
                        leave_btn = self.page.locator('[aria-label*="Sair"]')
                        count = await leave_btn.count()
                        if count > 0:
                            logger.info(f"Found {count} elements with aria-label containing 'Sair' - we're in the meeting!")
                            return
                    except Exception as e:
                        logger.debug(f"Locator check failed: {e}")

                    # Also try direct attribute check
                    try:
                        buttons = await self.page.query_selector_all('button')
                        for btn in buttons[:20]:  # Check first 20 buttons
                            label = await btn.get_attribute('aria-label')
                            if label and ('Sair' in label or 'Leave' in label):
                                logger.info(f"Found button with label '{label}' - we're in the meeting!")
                                return
                    except Exception as e:
                        logger.debug(f"Button scan failed: {e}")

            # Log progress every 10 seconds
            if i > 0 and i % 10 == 0:
                logger.info(f"Still waiting for admission... ({i}s) in_waiting={in_waiting}")
                await self.page.screenshot(path=f"/recordings/waiting_{i}s.png")

            await asyncio.sleep(1)

        # Take final screenshot before timeout
        await self._capture_diagnostic_info("join_timeout")
        raise TimeoutError(f"Failed to join meeting within {config.JOIN_TIMEOUT} seconds")
    
    async def start_recording(self):
        """Start recording the meeting"""
        logger.info("Starting recording...")
        await self.recorder.start()
        
        # Start caption scraping for speaker detection
        if self.page:
            self.caption_scraper = CaptionScraper(self.page)
            # Enable captions (needed for speaker detection)
            await self.caption_scraper.enable_captions()
            await self.caption_scraper.start_scraping()
    
    async def stop_recording(self):
        """Stop recording"""
        logger.info("Stopping recording...")
        
        # Stop caption scraping
        if self.caption_scraper:
            await self.caption_scraper.stop_scraping()
        
        return await self.recorder.stop()
    
    async def upload_recording(self, recording_path) -> str:
        """Upload recording to R2"""
        logger.info("Uploading recording to R2...")
        storage_path = self.uploader.upload_recording(
            recording_path,
            self.user_id,
            self.meeting_id
        )
        logger.info(f"Recording uploaded: {storage_path}")
        return storage_path
    
    async def monitor_meeting(self):
        """Monitor the meeting and detect when it ends"""
        logger.info("Monitoring meeting...")
        
        while self.is_in_meeting and not self.meeting_ended:
            # Check if we've been removed or meeting ended
            if await self._check_meeting_ended():
                logger.info("Meeting ended detected")
                self.meeting_ended = True
                break
            
            # Check max duration
            if await self.recorder.is_max_duration_reached():
                logger.info("Max duration reached")
                self.meeting_ended = True
                break
            
            await asyncio.sleep(5)
    
    async def _check_meeting_ended(self) -> bool:
        """Check if the meeting has ended"""
        # Look for signs that meeting ended (EN + PT-BR variations)
        end_indicators = [
            # Left the meeting
            'text="You left the meeting"',
            'text="Você saiu da reunião"',
            'text="You\'ve left the meeting"',
            # Meeting ended
            'text="The meeting has ended"',
            'text="A reunião terminou"',
            'text="This meeting has ended"',
            'text="Esta reunião terminou"',
            # Removed from meeting
            'text="You have been removed"',
            'text="Você foi removido"',
            'text="You\'ve been removed from the meeting"',
            'text="Você foi removido da reunião"',
            'text="You were removed from the meeting"',
            # Return to home screen indicators
            'text="Return to home screen"',
            'text="Voltar para a tela inicial"',
            'text="Rejoin"',
            'text="Voltar para a reunião"',
        ]

        for indicator in end_indicators:
            try:
                elem = await self.page.query_selector(indicator)
                if elem:
                    logger.info(f"Meeting ended - detected: {indicator}")
                    return True
            except Exception:
                pass

        # Check if we're still on a meet page
        try:
            url = self.page.url
            if "meet.google.com" not in url:
                logger.info(f"Meeting ended - no longer on meet.google.com: {url}")
                return True
        except Exception:
            pass

        # Check if meeting indicators disappeared (we were kicked out)
        try:
            # If we were in a meeting, these should exist
            participant_tile = await self.page.query_selector('[data-participant-id]')
            leave_button = await self.page.query_selector('[aria-label="Sair da chamada"]')
            mute_indicator = await self.page.query_selector('[data-is-muted]')

            # If ALL key indicators are gone, we're probably out of the meeting
            if not participant_tile and not leave_button and not mute_indicator:
                # Double-check by looking for post-meeting UI
                rejoin_btn = await self.page.query_selector('button:has-text("Rejoin"), button:has-text("Voltar")')
                if rejoin_btn:
                    logger.info("Meeting ended - found rejoin button, all meeting indicators gone")
                    return True
        except Exception:
            pass

        return False
    
    async def leave_meeting(self):
        """Leave the meeting"""
        logger.info("Leaving meeting...")
        
        try:
            leave_btn = await self.page.query_selector(
                '[aria-label*="Leave call"], '
                '[aria-label*="Sair da chamada"], '
                'button[aria-label*="leave"]'
            )
            if leave_btn:
                await leave_btn.click()
                logger.info("Clicked leave button")
        except Exception as e:
            logger.debug(f"Could not click leave button: {e}")
        
        self.is_in_meeting = False
    
    async def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up...")
        
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
        
        logger.info("Cleanup complete")
    
    def get_duration_seconds(self) -> int:
        """Get meeting duration in seconds"""
        if not self.start_time:
            return 0
        return int((datetime.now() - self.start_time).total_seconds())
