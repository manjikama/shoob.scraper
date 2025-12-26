#!/usr/bin/env python3
"""
Advanced Event-Driven Shoob.gg Card Scraper
===========================================

Smart browser-based scraper that waits for actual data loading events
instead of fixed delays. Event-driven approach for maximum efficiency.

Features:
- Event-driven waiting (no fixed delays)
- Smart element detection
- Adaptive timeouts based on actual loading
- Maximum efficiency with browser reliability
- Live-save functionality
- Resume capability

Author: Senior Developer
Version: 1.0.0-advanced
"""

import asyncio
import json
import logging
import re
import time
import sys
import signal
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from urllib.parse import urljoin
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler

from playwright.async_api import async_playwright, Page, Browser, BrowserContext, TimeoutError

# Import configuration
from config import (
    SCRAPING_CONFIG, BROWSER_CONFIG, URLS, DATA_CONFIG, LOGGING_CONFIG,
    SELECTORS, ERROR_CONFIG, PERFORMANCE_CONFIG, OUTPUT_DIR, SCRAPER_VERSION,
    WAIT_SELECTORS
)


class AdvancedShoobCardScraper:
    """
    Advanced event-driven web scraper for Shoob.gg cards.
    
    Features:
    - Event-driven waiting (waits for actual data, not fixed time)
    - Smart element detection and adaptive timeouts
    - Maximum efficiency while maintaining browser reliability
    - Live-save functionality and resume capability
    - Performance tracking with wait time analytics
    """
    
    def __init__(self):
        """Initialize the advanced scraper with smart waiting."""
        self.config = SCRAPING_CONFIG
        self.browser_config = BROWSER_CONFIG
        self.urls = URLS
        self.data_config = DATA_CONFIG
        self.selectors = SELECTORS
        self.wait_selectors = WAIT_SELECTORS
        
        # Initialize data storage
        self.all_cards: List[Dict[str, Any]] = []
        self.scraped_pages: Set[int] = set()
        self.failed_card_ids: Set[str] = set()  # Track failed cards for retry
        self.session_id = f"advanced_session_{int(time.time())}"
        
        # Browser cleanup tracking
        self.browser = None
        self.context = None
        self.page = None
        self.cleanup_done = False
        
        # Performance tracking
        self.wait_times = {
            "page_loads": [],
            "card_loads": [],
            "element_waits": [],
            "total_saved": 0
        }
        
        # Setup logging
        self._setup_logging()
        
        # Initialize statistics
        self.stats = {
            "start_time": None,
            "pages_scraped": 0,
            "cards_extracted": 0,
            "pages_skipped": 0,
            "errors": 0,
            "consecutive_errors": 0,
            "total_requests": 0,
            "success_rate": 0.0,
            "total_wait_time": 0.0,
            "average_wait_per_page": 0.0,
            "average_wait_per_card": 0.0,
        }
        
        # Ensure output directory exists
        OUTPUT_DIR.mkdir(exist_ok=True)
        
        self.logger.info(f"🚀 Advanced Event-Driven Shoob Card Scraper v{SCRAPER_VERSION} initialized")
        self.logger.info(f"⚡ Smart waiting enabled - no fixed delays!")
        self.logger.info(f"📁 Output directory: {OUTPUT_DIR}")
        
    def _setup_logging(self) -> None:
        """Setup professional logging configuration with error file logging."""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(LOGGING_CONFIG["level"])
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Console handler (clean output)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(LOGGING_CONFIG["level"])
        
        # Create formatter
        formatter = logging.Formatter(
            LOGGING_CONFIG["format"],
            datefmt=LOGGING_CONFIG["date_format"]
        )
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler for errors only
        if LOGGING_CONFIG.get("log_to_file", True):
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            
            log_file = log_dir / LOGGING_CONFIG.get("log_file", "scraper_errors.log")
            
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=LOGGING_CONFIG.get("max_log_size_mb", 10) * 1024 * 1024,
                backupCount=LOGGING_CONFIG.get("backup_count", 3),
                encoding='utf-8'  # Use UTF-8 encoding for emoji support
            )
            file_handler.setLevel(logging.WARNING)  # Only warnings and errors to file
            
            # Detailed formatter for file logging
            file_formatter = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(funcName)s:%(lineno)d | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
            
            # Create separate file logger for clean console output
            self._file_logger = logging.getLogger(f"{__name__}_file")
            self._file_logger.setLevel(logging.WARNING)
            self._file_logger.handlers.clear()
            self._file_logger.addHandler(file_handler)
            self._file_logger.propagate = False
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def _log_to_file_only(self, message: str, level: str = "WARNING") -> None:
        """Log message to file only, not console, to keep progress display clean."""
        if hasattr(self, '_file_logger'):
            if level.upper() == "ERROR":
                self._file_logger.error(message)
            elif level.upper() == "INFO":
                self._file_logger.info(message)
            else:
                self._file_logger.warning(message)
    
    def _load_progress(self) -> Dict[str, Any]:
        """Load scraping progress from file."""
        progress_file = OUTPUT_DIR / self.config["resume_file"]
        
        if not progress_file.exists() or not self.config["enable_resume"]:
            return {"scraped_pages": [], "total_cards": 0}
        
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress = json.load(f)
            
            self.scraped_pages = set(progress.get("scraped_pages", []))
            if self.scraped_pages:
                self.logger.info(f"📂 Resume: Found {len(self.scraped_pages)} previously scraped pages")
            
            return progress
            
        except Exception as e:
            self._log_to_file_only(f"Could not load progress file: {e}")
            return {"scraped_pages": [], "total_cards": 0}
    
    def _save_progress(self) -> None:
        """Save current scraping progress."""
        if not self.config["enable_resume"]:
            return
            
        progress_file = OUTPUT_DIR / self.config["resume_file"]
        
        try:
            progress_data = {
                "session_id": self.session_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "scraped_pages": sorted(list(self.scraped_pages)),
                "total_cards": len(self.all_cards),
                "stats": self.stats,
                "wait_times": self.wait_times
            }
            
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, indent=2)
                
        except Exception as e:
            self._log_to_file_only(f"Could not save progress: {e}")
    
    def _save_after_page(self, page_num: int, cards_count: int) -> None:
        """Save all data after each page."""
        try:
            # Save progress tracking
            self._save_progress()
            
            # Save complete data file if live-save is enabled
            if self.config.get("live_save", True):
                output_file = self._save_final_output()
                self.logger.info(f"💾 Live-save: Page {page_num} completed ({cards_count} cards) - Total: {len(self.all_cards)} cards")
            else:
                self.logger.info(f"✅ Page {page_num} completed ({cards_count} cards) - Total: {len(self.all_cards)} cards")
            
        except Exception as e:
            self._log_to_file_only(f"Could not save after page {page_num}: {e}")
    
    async def _setup_browser(self) -> tuple[Browser, BrowserContext, Page]:
        """Setup browser with professional anti-detection measures."""
        self.logger.info("🔧 Setting up advanced browser with smart waiting")
        
        playwright = await async_playwright().start()
        
        browser = await playwright.chromium.launch(
            headless=self.browser_config["headless"],
            args=self.browser_config["browser_args"]
        )
        
        context = await browser.new_context(
            user_agent=self.browser_config["user_agent"],
            viewport=self.browser_config["viewport"],
            locale=self.browser_config["locale"],
            timezone_id=self.browser_config["timezone"]
        )
        
        # Advanced anti-detection measures
        await context.add_init_script("""
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Remove automation indicators
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
            
            // Override permissions
            Object.defineProperty(navigator, 'permissions', {
                get: () => ({
                    query: () => Promise.resolve({ state: 'granted' })
                })
            });
            
            // Override plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """)
        
        page = await context.new_page()
        
        # Set additional headers
        await page.set_extra_http_headers(self.browser_config["extra_headers"])
        
        return browser, context, page
    
    async def _cleanup_browser(self):
        """Safely cleanup browser resources."""
        if self.cleanup_done:
            return
            
        self.cleanup_done = True
        
        try:
            # Close page first
            if self.page and not self.page.is_closed():
                await self.page.close()
                await asyncio.sleep(0.1)
        except Exception:
            pass
        
        try:
            # Close context
            if self.context:
                await self.context.close()
                await asyncio.sleep(0.1)
        except Exception:
            pass
        
        try:
            # Close browser and wait for subprocess cleanup
            if self.browser:
                await self.browser.close()
                await asyncio.sleep(0.2)
        except Exception:
            pass
        
        # Additional cleanup for Windows
        try:
            import sys
            if sys.platform == "win32":
                await asyncio.sleep(0.3)
        except Exception:
            pass
    
    async def _smart_wait_for_element(self, selector: str, timeout: int = None, description: str = "") -> bool:
        """Smart wait for element with performance tracking."""
        if timeout is None:
            timeout = self.config["max_wait_timeout"]
        
        start_time = time.time()
        
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            wait_time = time.time() - start_time
            self.wait_times["element_waits"].append(wait_time)
            self.stats["total_wait_time"] += wait_time
            
            return True
            
        except TimeoutError:
            wait_time = time.time() - start_time
            # Log timeout to file only (not console to keep progress clean)
            self._log_to_file_only(f"Timeout after {wait_time:.2f}s waiting for {selector} ({description})")
            return False
        except Exception as e:
            wait_time = time.time() - start_time
            # Log error to file only (not console to keep progress clean)
            self._log_to_file_only(f"Error waiting for {selector}: {e}")
            return False
    
    async def _smart_wait_for_cards_loaded(self) -> bool:
        """Wait for cards to be loaded on the page with flexible detection."""
        # Strategy 1: Wait for at least one card link (quick check)
        if await self._smart_wait_for_element(
            self.wait_selectors["cards_container"], 
            5000,  # Shorter timeout for first card
            "First card link"
        ):
            # Strategy 2: Wait a bit for more cards to load
            await asyncio.sleep(self.config["network_settle_time"])
            
            # Strategy 3: Check how many cards we have
            try:
                card_count = await self.page.locator(self.wait_selectors["cards_container"]).count()
                
                if card_count >= 5:
                    # We have a good number of cards, proceed
                    return True
                elif card_count > 0:
                    # We have some cards, wait a bit more for others
                    await asyncio.sleep(1.0)
                    
                    # Check again
                    final_count = await self.page.locator(self.wait_selectors["cards_container"]).count()
                    return final_count > 0
                else:
                    return False
                    
            except Exception as e:
                return True  # Proceed if we can't count
        
        return False
    
    async def _smart_wait_for_card_data(self) -> bool:
        """Wait for card data to be loaded on individual card page with flexible fallbacks."""
        # Strategy 1: Wait for any meta title (more flexible)
        meta_loaded = await self._smart_wait_for_element(
            "meta[property='og:title'], title",
            5000,  # Shorter timeout for basic elements
            "Basic card title"
        )
        
        if meta_loaded:
            # Strategy 2: Small delay for DOM to stabilize, then check for content
            await asyncio.sleep(self.config["network_settle_time"])
            
            # Strategy 3: Verify we have actual content (not just empty tags)
            try:
                title_content = await self.page.evaluate("""
                    () => {
                        const ogTitle = document.querySelector('meta[property="og:title"]');
                        const pageTitle = document.querySelector('title');
                        
                        const ogContent = ogTitle ? ogTitle.getAttribute('content') : '';
                        const titleContent = pageTitle ? pageTitle.textContent : '';
                        
                        return {
                            og_title: ogContent,
                            page_title: titleContent,
                            has_content: !!(ogContent || titleContent)
                        };
                    }
                """)
                
                if title_content.get('has_content'):
                    return True
                else:
                    await asyncio.sleep(1.0)  # Wait a bit more for content to populate
                    return True  # Proceed anyway, extraction will handle empty content
            
            except Exception as e:
                return True  # Proceed if we can't check content
        
        # Strategy 4: Fallback - wait for any page content
        content_loaded = await self._smart_wait_for_element(
            "body, main, .container",
            3000,
            "Basic page content"
        )
        
        if content_loaded:
            await asyncio.sleep(self.config["minimal_delay"])
            return True
        
        # Strategy 5: Last resort - if we're here, the page might be loaded but slow
        return True  # Proceed anyway and let extraction handle what's available
    
    async def _get_card_links_from_page(self, page_num: int) -> List[str]:
        """Extract card links with smart waiting."""
        url = f"{self.urls['base_url']}?page={page_num}"
        
        for attempt in range(self.config["retry_attempts"]):
            try:
                self.logger.debug(f"🔍 Getting cards from page {page_num} (attempt {attempt + 1})")
                
                # Navigate and wait for network to be idle
                page_start_time = time.time()
                await self.page.goto(url, wait_until="networkidle", timeout=self.config["page_load_timeout"])
                
                # Smart wait for cards to load
                cards_loaded = await self._smart_wait_for_cards_loaded()
                
                if not cards_loaded:
                    self._log_to_file_only(f"Cards didn't load properly on page {page_num}")
                    continue
                
                page_load_time = time.time() - page_start_time
                self.wait_times["page_loads"].append(page_load_time)
                
                # Extract card links immediately once loaded
                card_links = []
                for selector in self.selectors["card_links"]:
                    link_elements = await self.page.locator(selector).all()
                    
                    for link_element in link_elements:
                        href = await link_element.get_attribute("href")
                        if href:
                            full_url = urljoin(self.urls["site_url"], href)
                            card_links.append(full_url)
                
                # Remove duplicates while preserving order
                unique_links = list(dict.fromkeys(card_links))
                
                if unique_links:
                    self.logger.info(f"✅ Page {page_num}: Found {len(unique_links)} cards")
                    self.stats["consecutive_errors"] = 0
                    return unique_links
                else:
                    self._log_to_file_only(f"Page {page_num}: No cards found")
                    return []
                
            except Exception as e:
                self._log_to_file_only(f"Attempt {attempt + 1} failed for page {page_num}: {e}")
                self.stats["errors"] += 1
                self.stats["consecutive_errors"] += 1
                
                if attempt < self.config["retry_attempts"] - 1:
                    await asyncio.sleep(self.config["retry_delay"])
                else:
                    self._log_to_file_only(f"Failed to get cards from page {page_num} after all attempts", "ERROR")
                    return []
    
    async def _extract_card_data(self, card_url: str, page_num: int = None) -> Optional[Dict[str, Any]]:
        """Extract card data with smart waiting and robust error handling."""
        card_id = re.search(r'/cards/info/([a-f0-9]+)', card_url)
        card_id = card_id.group(1) if card_id else "unknown"
        
        for attempt in range(self.config["retry_attempts"]):
            try:
                # Navigate with smart waiting
                card_start_time = time.time()
                await self.page.goto(card_url, wait_until="domcontentloaded", timeout=self.config["page_load_timeout"])
                
                # Smart wait for card data to be loaded (more flexible now)
                data_loaded = await self._smart_wait_for_card_data()
                
                if not data_loaded:
                    self._log_to_file_only(f"Card data didn't load properly for {card_id}, but proceeding with extraction")
                
                card_load_time = time.time() - card_start_time
                self.wait_times["card_loads"].append(card_load_time)
                
                # Extract meta tags immediately once loaded (or after timeout)
                meta_data = await self._extract_meta_tags()
                
                # Initialize card data (without load_time)
                card_data = {
                    "card_id": card_id,
                    "card_url": card_url,
                    "page_num": page_num,
                    "extraction_timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                # Fast extraction using meta tags (most reliable and fastest)
                card_data["name"] = self._extract_name_fast(meta_data)
                card_data["character_source"] = self._extract_character_source_fast(meta_data)
                card_data["series"] = card_data["character_source"]
                card_data["creator"] = self._extract_creator_fast(meta_data)
                card_data["card_maker"] = card_data["creator"]
                card_data["description"] = self._extract_description_fast(meta_data)
                card_data["last_updated"] = meta_data.get("meta_property_og:updated_time", "")
                
                # Fast tier extraction
                card_data["tier"] = await self._extract_tier_fast(meta_data)
                
                # Fast image extraction
                image_urls = self._extract_images_fast(meta_data, card_id)
                card_data.update(image_urls)
                
                # Add metadata if configured
                if self.config["include_metadata"]:
                    card_data["metadata"] = meta_data
                
                # Clean up empty fields
                card_data = {k: v for k, v in card_data.items() if v not in ["", {}, []]}
                
                # More lenient validation - accept cards even if some data is missing
                if card_data.get("card_id") and (card_data.get("name") or card_data.get("image_url")):
                    self.stats["cards_extracted"] += 1
                    self.stats["consecutive_errors"] = 0
                    return card_data
                else:
                    # Still return the card data even if validation fails
                    self._log_to_file_only(f"Card {card_id} has minimal data but including it anyway")
                    self.stats["cards_extracted"] += 1
                    return card_data
                    
            except Exception as e:
                self._log_to_file_only(f"Attempt {attempt + 1} failed for card {card_id}: {e}")
                self.stats["errors"] += 1
                self.stats["consecutive_errors"] += 1
                
                if attempt < self.config["retry_attempts"] - 1:
                    await asyncio.sleep(self.config["retry_delay"])
                else:
                    self._log_to_file_only(f"Failed to extract card {card_id} after all attempts", "ERROR")
                    self.failed_card_ids.add(card_id)  # Track failed card for potential retry
                    return None
    
    async def _extract_meta_tags(self) -> Dict[str, str]:
        """Extract meta tags efficiently using JavaScript evaluation."""
        try:
            meta_data = await self.page.evaluate("""
                () => {
                    const meta = {};
                    
                    // Get all meta tags
                    document.querySelectorAll('meta').forEach(tag => {
                        const name = tag.getAttribute('name');
                        const property = tag.getAttribute('property');
                        const content = tag.getAttribute('content');
                        
                        if (content) {
                            if (name) meta[`meta_name_${name}`] = content;
                            if (property) meta[`meta_property_${property}`] = content;
                        }
                    });
                    
                    // Get page title
                    meta.page_title = document.title;
                    
                    return meta;
                }
            """)
            
            return meta_data
            
        except Exception as e:
            self._log_to_file_only(f"Error extracting meta tags: {e}")
            return {}
    
    def _extract_name_fast(self, meta_data: Dict[str, str]) -> str:
        """Fast name extraction using meta tags only."""
        og_title = meta_data.get("meta_property_og:title", "")
        if og_title and og_title != "Card preview":
            return self._clean_text(og_title)
        
        page_title = meta_data.get("page_title", "")
        if page_title and "|" in page_title:
            name = page_title.split("|")[0].strip()
            if name != "Card preview":
                return self._clean_text(name)
        
        return "Unknown Card"
    
    def _extract_character_source_fast(self, meta_data: Dict[str, str]) -> str:
        """Fast character source extraction using meta tags only."""
        description = meta_data.get("meta_name_description", "")
        if description:
            from_match = re.search(r'from\s+([^\n\\]+?)(?:\n|\\n|Creators:|$)', description)
            if from_match:
                series = from_match.group(1).strip()
                series = re.sub(r'\s*Creators:.*', '', series)
                series = re.sub(r'\s*-\s*Card Maker:.*', '', series)
                return self._clean_text(series)
        
        return "Unknown Series"
    
    def _extract_creator_fast(self, meta_data: Dict[str, str]) -> str:
        """Fast creator extraction using meta tags only."""
        description = meta_data.get("meta_name_description", "")
        if description:
            creator_patterns = [
                r'Card Maker:\s*([^\n\\]+)',
                r'Creators:\s*-\s*Card Maker:\s*([^\n\\]+)',
                r'- Card Maker:\s*([^\n\\]+)'
            ]
            
            for pattern in creator_patterns:
                match = re.search(pattern, description, re.IGNORECASE)
                if match:
                    creator = match.group(1).strip()
                    creator = re.sub(r'&[^;]+;', '', creator)
                    creator = re.sub(r'\\n.*', '', creator)
                    return self._clean_text(creator)
        
        return ""
    
    def _extract_description_fast(self, meta_data: Dict[str, str]) -> str:
        """Fast description extraction using meta tags only."""
        description = meta_data.get("meta_name_description", "")
        if description and "Here you can preview" not in description:
            return self._clean_text(description)
        
        og_description = meta_data.get("meta_property_og:description", "")
        if og_description and og_description != description and "Here you can preview" not in og_description:
            return self._clean_text(og_description)
        
        return ""
    
    async def _extract_tier_fast(self, meta_data: Dict[str, str]) -> str:
        """Fast tier extraction using meta tags only."""
        
        # Strategy 1: Extract from image URL (fastest and most reliable)
        og_image = meta_data.get("meta_property_og:image", "")
        if og_image:
            tier_in_url = re.search(r'/cards/([0-9S])/', og_image, re.IGNORECASE)
            if tier_in_url:
                tier = tier_in_url.group(1)
                if tier in ['1', '2', '3', '4', '5', 'S', 's']:
                    return tier.upper() if tier.lower() == 's' else tier
        
        # Strategy 2: Meta tags (fallback)
        for meta_text in [meta_data.get("meta_property_og:title", ""), meta_data.get("page_title", "")]:
            if meta_text:
                tier_match = re.search(r'tier[:\s]*([0-9S]+)', meta_text, re.IGNORECASE)
                if tier_match and tier_match.group(1) in ['1', '2', '3', '4', '5', 'S', 's']:
                    return tier_match.group(1).upper() if tier_match.group(1).lower() == 's' else tier_match.group(1)
        
        return "Unknown"
    
    def _extract_images_fast(self, meta_data: Dict[str, str], card_id: str) -> Dict[str, str]:
        """Fast image extraction using meta tags only."""
        image_data = {}
        
        og_image = meta_data.get("meta_property_og:image", "")
        if og_image:
            image_data["og_image"] = og_image
            image_data["high_res_image_url"] = og_image
            image_data["image_url"] = og_image
        
        twitter_image = meta_data.get("meta_name_twitter:image", "")
        if twitter_image:
            image_data["twitter_image"] = twitter_image
            if not image_data.get("image_url"):
                image_data["image_url"] = twitter_image
        
        # API fallback
        if not image_data.get("image_url"):
            image_data["image_url"] = f"{self.urls['api_base']}/cardr/{card_id}?size=700"
        
        return image_data
    
    def _validate_card_data_fast(self, card_data: Dict[str, Any]) -> bool:
        """Fast validation with minimal checks."""
        return (
            card_data.get("name", "") not in ["", "Unknown Card", "Card preview"] and
            card_data.get("card_id", "") != ""
        )
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text with configuration options."""
        if not text:
            return ""
        
        if not self.data_config["clean_text"]:
            return text
        
        # Remove extra whitespace and newlines
        if self.data_config["remove_extra_whitespace"]:
            cleaned = re.sub(r'\s+', ' ', text.strip())
            cleaned = re.sub(r'[\r\n\t]', ' ', cleaned)
            cleaned = re.sub(r'\\n', ' ', cleaned)
            cleaned = cleaned.strip()
        else:
            cleaned = text.strip()
        
        return cleaned
    
    async def _scrape_page(self, page_num: int) -> List[Dict[str, Any]]:
        """Scrape all cards from a single page with professional progress indicators."""
        
        try:
            # Get card links from the page (with smart waiting)
            card_links = await self._get_card_links_from_page(page_num)
            
            if not card_links:
                self._log_to_file_only(f"No cards found on page {page_num}")
                return []
            
            # Extract data from each card with clean progress indicator
            page_cards = []
            total_cards = len(card_links)
            
            for i, card_url in enumerate(card_links, 1):
                try:
                    # Clean progress indicator that updates in place - write to stderr to avoid logger capture
                    progress_text = f"🔄 Processing cards: [{i}/{total_cards}] ({i/total_cards*100:.0f}%)"
                    sys.stderr.write(f"\r{progress_text:<60}")
                    sys.stderr.flush()
                    
                    card_data = await self._extract_card_data(card_url, page_num)
                    if card_data:
                        page_cards.append(card_data)
                    
                    # Minimal delay only if needed for rate limiting
                    if i < total_cards:
                        await asyncio.sleep(self.config["minimal_delay"])
                        
                except Exception as e:
                    # Log errors to file only to keep console clean
                    self._log_to_file_only(f"Error processing card {i}/{total_cards}: {e}", "ERROR")
                    self.stats["errors"] += 1
                    continue
            
            # Clear progress line and show final result
            final_text = f"✅ Page {page_num}: Extracted {len(page_cards)}/{total_cards} cards"
            sys.stderr.write(f"\r{final_text:<60}\n")
            sys.stderr.flush()
            self.stats["pages_scraped"] += 1
            
            # Add cards to main collection
            self.all_cards.extend(page_cards)
            self.scraped_pages.add(page_num)
            
            # Save after each page (live-save functionality)
            self._save_after_page(page_num, len(page_cards))
            
            return page_cards
            
        except Exception as e:
            self._log_to_file_only(f"Error scraping page {page_num}: {e}", "ERROR")
            self.stats["errors"] += 1
            return []
    
    def _calculate_statistics(self) -> Dict[str, Any]:
        """Calculate comprehensive scraping statistics with wait time analytics."""
        if self.stats["start_time"]:
            elapsed_time = time.time() - self.stats["start_time"]
            cards_per_second = self.stats["cards_extracted"] / elapsed_time if elapsed_time > 0 else 0
            pages_per_minute = (self.stats["pages_scraped"] / elapsed_time) * 60 if elapsed_time > 0 else 0
        else:
            elapsed_time = 0
            cards_per_second = 0
            pages_per_minute = 0
        
        total_operations = self.stats["pages_scraped"] + self.stats["errors"]
        success_rate = (self.stats["pages_scraped"] / total_operations * 100) if total_operations > 0 else 0
        
        # Calculate wait time statistics
        avg_page_wait = sum(self.wait_times["page_loads"]) / len(self.wait_times["page_loads"]) if self.wait_times["page_loads"] else 0
        avg_card_wait = sum(self.wait_times["card_loads"]) / len(self.wait_times["card_loads"]) if self.wait_times["card_loads"] else 0
        total_wait_time = self.stats["total_wait_time"]
        
        return {
            "session_id": self.session_id,
            "pages_scraped": self.stats["pages_scraped"],
            "pages_skipped": self.stats["pages_skipped"],
            "cards_extracted": self.stats["cards_extracted"],
            "total_errors": self.stats["errors"],
            "success_rate": round(success_rate, 2),
            "elapsed_time": round(elapsed_time, 2),
            "cards_per_second": round(cards_per_second, 2),
            "pages_per_minute": round(pages_per_minute, 2),
            "average_cards_per_page": round(self.stats["cards_extracted"] / max(self.stats["pages_scraped"], 1), 1),
            "wait_time_analytics": {
                "total_wait_time": round(total_wait_time, 2),
                "average_page_load": round(avg_page_wait, 2),
                "average_card_load": round(avg_card_wait, 2),
                "wait_efficiency": round((elapsed_time - total_wait_time) / elapsed_time * 100, 1) if elapsed_time > 0 else 0
            }
        }
    
    def _save_final_output(self) -> Path:
        """Save cards to data.json and progress to process.json."""
        data_file = OUTPUT_DIR / "data.json"
        process_file = OUTPUT_DIR / "process.json"
        
        try:
            # Save simple data.json with just cards
            data_output = {
                "cards": self.all_cards,
                "total": len(self.all_cards),
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(
                    data_output,
                    f,
                    ensure_ascii=False,
                    indent=2 if self.config["pretty_print"] else None
                )
            
            # Save process.json with progress tracking
            process_output = {
                "scraped_pages": sorted(list(self.scraped_pages)),
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "total_cards": len(self.all_cards),
                "scraper_version": SCRAPER_VERSION,
                "session_statistics": self._calculate_statistics()
            }
            
            with open(process_file, 'w', encoding='utf-8') as f:
                json.dump(
                    process_output,
                    f,
                    ensure_ascii=False,
                    indent=2 if self.config["pretty_print"] else None
                )
            
            self.logger.info(f"💾 Data saved to: {data_file}")
            self.logger.info(f"📊 Progress saved to: {process_file}")
            self.logger.info(f"🃏 Total cards: {len(self.all_cards)}")
            
            return data_file
            
        except Exception as e:
            self.logger.error(f"❌ Error saving output: {e}")
            raise
    
    async def scrape_all_pages(self, start_page: Optional[int] = None, end_page: Optional[int] = None) -> Dict[str, Any]:
        """Main scraping method with smart waiting and performance tracking."""
        # Initialize
        self.stats["start_time"] = time.time()
        start_page = start_page or self.config["start_page"]
        end_page = end_page or self.config["end_page"]
        
        # Load previous progress
        self._load_progress()
        
        # Setup browser
        self.browser, self.context, self.page = await self._setup_browser()
        
        try:
            # Determine pages to scrape
            if end_page is None:
                end_page = 100  # Reasonable default
                self.logger.info(f"📊 No end page specified, will scrape up to page {end_page}")
            
            pages_to_scrape = []
            for page_num in range(start_page, end_page + 1):
                if page_num not in self.scraped_pages:
                    pages_to_scrape.append(page_num)
                else:
                    self.stats["pages_skipped"] += 1
            
            self.logger.info(f"📊 Smart Scraping Plan:")
            self.logger.info(f"   Pages range: {start_page} to {end_page}")
            self.logger.info(f"   Pages to scrape: {len(pages_to_scrape)}")
            self.logger.info(f"   Pages to skip: {len(self.scraped_pages)}")
            self.logger.info(f"   Method: Event-driven smart waiting")
            self.logger.info("-" * 60)
            
            # Check for consecutive errors
            consecutive_error_limit = ERROR_CONFIG["max_consecutive_errors"]
            
            # Scrape pages with smart waiting
            for page_num in pages_to_scrape:
                try:
                    # Check consecutive error limit
                    if self.stats["consecutive_errors"] >= consecutive_error_limit:
                        self.logger.error(f"❌ Too many consecutive errors ({consecutive_error_limit}), stopping")
                        break
                    
                    # Log which page we're scraping
                    self.logger.info(f"🚀 Scraping page {page_num}")
                    
                    # Scrape the page with smart waiting
                    await self._scrape_page(page_num)
                    
                    # Progress update
                    if LOGGING_CONFIG["show_progress"]:
                        progress = (len(self.scraped_pages) / len(pages_to_scrape)) * 100
                        self.logger.info(f"📈 Progress: {progress:.1f}% ({len(self.scraped_pages)}/{len(pages_to_scrape)} pages)")
                    
                    # Minimal delay between pages (only for rate limiting)
                    if page_num < max(pages_to_scrape):
                        await asyncio.sleep(self.config["minimal_delay"])
                    
                except Exception as e:
                    self._log_to_file_only(f"Critical error processing page {page_num}: {e}", "ERROR")
                    self.stats["errors"] += 1
                    self.stats["consecutive_errors"] += 1
                    
                    if ERROR_CONFIG["continue_on_error"]:
                        await asyncio.sleep(ERROR_CONFIG["error_cooldown"])
                        continue
                    else:
                        break
            
            # Retry failed cards if any
            if self.failed_card_ids and len(self.failed_card_ids) <= 10:  # Only retry if reasonable number
                self.logger.info(f"🔄 Retrying {len(self.failed_card_ids)} failed cards...")
                await self._retry_failed_cards()
            
            # Calculate and display final statistics
            final_stats = self._calculate_statistics()
            
            if LOGGING_CONFIG["show_statistics"]:
                self.logger.info("🎉 Smart scraping completed!")
                self.logger.info(f"📊 Final Statistics:")
                self.logger.info(f"   Pages scraped: {final_stats['pages_scraped']}")
                self.logger.info(f"   Pages skipped: {final_stats['pages_skipped']}")
                self.logger.info(f"   Cards extracted: {final_stats['cards_extracted']}")
                self.logger.info(f"   Success rate: {final_stats['success_rate']}%")
                self.logger.info(f"   Total time: {final_stats['elapsed_time']}s")
                self.logger.info(f"   Speed: {final_stats['cards_per_second']} cards/sec")
                self.logger.info(f"   Average: {final_stats['average_cards_per_page']} cards/page")
                
                if self.failed_card_ids:
                    self.logger.warning(f"   Failed cards: {len(self.failed_card_ids)}")
                
                # Show wait time analytics
                wait_analytics = final_stats["wait_time_analytics"]
                self.logger.info(f"⏱️ Wait Time Analytics:")
                self.logger.info(f"   Total wait time: {wait_analytics['total_wait_time']}s")
                self.logger.info(f"   Avg page load: {wait_analytics['average_page_load']}s")
                self.logger.info(f"   Avg card load: {wait_analytics['average_card_load']}s")
                self.logger.info(f"   Wait efficiency: {wait_analytics['wait_efficiency']}%")
            
            # Save final output
            if self.all_cards:
                output_file = self._save_final_output()
                final_stats["output_file"] = str(output_file)
            else:
                self.logger.warning("⚠️ No cards were extracted")
            
            return final_stats
            
        except Exception as e:
            self.logger.error(f"❌ Critical error during scraping: {e}")
            raise
            
        finally:
            # Proper cleanup to prevent errors on exit
            await self._cleanup_browser()
    
    def get_scraped_data_summary(self) -> Dict[str, Any]:
        """Get a summary of scraped data."""
        output_file = OUTPUT_DIR / self.config["output_file"]
        
        summary = {
            "total_cards": len(self.all_cards),
            "scraped_pages": sorted(list(self.scraped_pages)),
            "output_file": str(output_file) if output_file.exists() else None,
            "session_id": self.session_id,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "scraper_type": "advanced_event_driven"
        }
        
        # Add file info if exists
        if output_file.exists():
            try:
                file_size = output_file.stat().st_size
                summary["file_size_mb"] = round(file_size / (1024 * 1024), 2)
                
                # Sample some cards for preview
                if self.all_cards:
                    sample_size = min(3, len(self.all_cards))
                    summary["sample_cards"] = [
                        {
                            "name": card.get("name", "Unknown"),
                            "tier": card.get("tier", "Unknown"),
                            "series": card.get("character_source", "Unknown")
                        }
                        for card in self.all_cards[:sample_size]
                    ]
                    
            except Exception as e:
                self._log_to_file_only(f"Error getting file info: {e}")
        
        return summary
    
    async def _retry_failed_cards(self) -> None:
        """Retry extraction for failed cards."""
        if not self.failed_card_ids:
            return
        
        failed_list = list(self.failed_card_ids)
        retry_success = 0
        
        for i, card_id in enumerate(failed_list, 1):
            try:
                progress_text = f"🔄 Retrying failed cards: [{i}/{len(failed_list)}] ({i/len(failed_list)*100:.0f}%)"
                sys.stderr.write(f"\r{progress_text:<60}")
                sys.stderr.flush()
                
                card_url = f"{self.urls['site_url']}/cards/info/{card_id}"
                card_data = await self._extract_card_data(card_url, None)  # Page unknown during retry
                
                if card_data:
                    self.all_cards.append(card_data)
                    self.failed_card_ids.remove(card_id)
                    retry_success += 1
                
                await asyncio.sleep(self.config["minimal_delay"])
                
            except Exception as e:
                self._log_to_file_only(f"Retry failed for card {card_id}: {e}", "ERROR")
        
        # Clear progress line and show result
        if retry_success > 0:
            final_text = f"🔄 Retry completed: {retry_success}/{len(failed_list)} cards recovered"
        else:
            final_text = f"🔄 Retry completed: No additional cards recovered"
        sys.stderr.write(f"\r{final_text:<60}\n")
        sys.stderr.flush()
