#!/usr/bin/env python3
"""
Professional Shoob.gg Card Scraper v2.0
=======================================

A robust, professional-grade web scraper for extracting card data from shoob.gg
with comprehensive data extraction, intelligent error handling, and optimized performance.

Features:
- Single-file output with all cards
- Python-based configuration system
- Professional logging with minimal noise
- Resume capability and progress tracking
- Comprehensive data extraction from individual card pages
- Anti-detection measures and rate limiting

Author: Senior Developer
Version: 2.0.0
"""

import asyncio
import json
import logging
import re
import time
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from urllib.parse import urljoin
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler

from playwright.async_api import async_playwright, Page, Browser, BrowserContext

# Import configuration
from config import (
    SCRAPING_CONFIG, BROWSER_CONFIG, URLS, DATA_CONFIG, LOGGING_CONFIG,
    SELECTORS, ERROR_CONFIG, PERFORMANCE_CONFIG, OUTPUT_DIR, SCRAPER_VERSION
)


class ShoobCardScraper:
    """
    Professional-grade web scraper for Shoob.gg cards.
    
    Features:
    - Single-file output with comprehensive card data
    - Python-based configuration system
    - Professional logging with performance tracking
    - Resume capability and progress tracking
    - Anti-detection measures and intelligent rate limiting
    - Comprehensive data extraction from individual card pages
    """
    
    def __init__(self):
        """Initialize the scraper with configuration."""
        self.config = SCRAPING_CONFIG
        self.browser_config = BROWSER_CONFIG
        self.urls = URLS
        self.data_config = DATA_CONFIG
        self.selectors = SELECTORS
        
        # Initialize data storage
        self.all_cards: List[Dict[str, Any]] = []
        self.scraped_pages: Set[int] = set()
        self.session_id = f"session_{int(time.time())}"
        
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
            "success_rate": 0.0
        }
        
        # Ensure output directory exists
        OUTPUT_DIR.mkdir(exist_ok=True)
        
        self.logger.info(f"🚀 Professional Shoob Card Scraper v{SCRAPER_VERSION} initialized")
        self.logger.info(f"📁 Output directory: {OUTPUT_DIR}")
        
    def _setup_logging(self) -> None:
        """Setup professional logging configuration."""
        # Create logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(LOGGING_CONFIG["level"])
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(LOGGING_CONFIG["level"])
        
        # Create formatter
        formatter = logging.Formatter(
            LOGGING_CONFIG["format"],
            datefmt=LOGGING_CONFIG["date_format"]
        )
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler (optional)
        if LOGGING_CONFIG["log_to_file"]:
            log_file = Path("logs") / LOGGING_CONFIG["log_file"]
            log_file.parent.mkdir(exist_ok=True)
            
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=LOGGING_CONFIG["max_log_size_mb"] * 1024 * 1024,
                backupCount=LOGGING_CONFIG["backup_count"]
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
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
            self.logger.warning(f"⚠️ Could not load progress file: {e}")
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
                "stats": self.stats
            }
            
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, indent=2)
                
        except Exception as e:
            self.logger.warning(f"⚠️ Could not save progress: {e}")
    
    async def _setup_browser(self) -> tuple[Browser, BrowserContext, Page]:
        """Setup browser with professional anti-detection measures."""
        self.logger.info("🔧 Setting up browser with anti-detection measures")
        
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
    
    async def _get_card_links_from_page(self, page: Page, page_num: int) -> List[str]:
        """Extract card links from a specific page with retry logic."""
        url = f"{self.urls['base_url']}?page={page_num}"
        
        for attempt in range(self.config["retry_attempts"]):
            try:
                self.logger.debug(f"🔍 Getting cards from page {page_num} (attempt {attempt + 1})")
                
                await page.goto(url, wait_until="networkidle", timeout=self.config["timeout"])
                await asyncio.sleep(2)  # Wait for dynamic content
                
                # Wait for cards to load
                await page.wait_for_selector("a[href*='/cards/info/']", timeout=10000)
                
                # Extract card links
                card_links = []
                for selector in self.selectors["card_links"]:
                    link_elements = await page.locator(selector).all()
                    
                    for link_element in link_elements:
                        href = await link_element.get_attribute("href")
                        if href:
                            full_url = urljoin(self.urls["site_url"], href)
                            card_links.append(full_url)
                
                # Remove duplicates while preserving order
                unique_links = list(dict.fromkeys(card_links))
                
                if unique_links:
                    self.logger.info(f"✅ Page {page_num}: Found {len(unique_links)} cards")
                    self.stats["consecutive_errors"] = 0  # Reset error counter
                    return unique_links
                else:
                    self.logger.warning(f"⚠️ Page {page_num}: No cards found")
                    return []
                
            except Exception as e:
                self.logger.warning(f"⚠️ Attempt {attempt + 1} failed for page {page_num}: {e}")
                self.stats["errors"] += 1
                self.stats["consecutive_errors"] += 1
                
                if attempt < self.config["retry_attempts"] - 1:
                    await asyncio.sleep(self.config["retry_delay"])
                else:
                    self.logger.error(f"❌ Failed to get cards from page {page_num} after all attempts")
                    return []
    
    async def _extract_card_data(self, page: Page, card_url: str) -> Optional[Dict[str, Any]]:
        """Extract comprehensive data with optimized speed while maintaining accuracy."""
        card_id = re.search(r'/cards/info/([a-f0-9]+)', card_url)
        card_id = card_id.group(1) if card_id else "unknown"
        
        for attempt in range(self.config["retry_attempts"]):
            try:
                await page.goto(card_url, wait_until="networkidle", timeout=self.config["timeout"])
                
                # Reduced wait time but still sufficient for accuracy
                await asyncio.sleep(2)  # Reduced from 5 to 2 seconds
                
                # Quick wait for essential elements only
                try:
                    await page.wait_for_selector("meta[property='og:title']", timeout=5000)  # Reduced timeout
                except:
                    pass  # Continue if not found quickly
                
                # Extract meta tags first (fastest and most reliable)
                meta_data = await self._extract_meta_tags(page)
                
                # Get HTML content once and process efficiently
                html_content = await page.content()
                main_card_html = await self._validate_main_card_section(html_content, card_id)
                
                # Initialize card data
                card_data = {
                    "card_id": card_id,
                    "card_url": card_url,
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
                
                # Fast tier extraction (optimized)
                card_data["tier"] = await self._extract_tier_fast(meta_data, main_card_html)
                
                # Fast image extraction
                image_urls = self._extract_images_fast(meta_data, card_id)
                card_data.update(image_urls)
                
                # Add metadata if configured
                if self.config["include_metadata"]:
                    card_data["metadata"] = meta_data
                
                # Clean up empty fields
                card_data = {k: v for k, v in card_data.items() if v not in ["", {}, []]}
                
                # Quick validation
                if self._validate_card_data_fast(card_data):
                    if LOGGING_CONFIG["show_card_details"]:
                        self.logger.info(f"⚡ Fast extraction: {card_data.get('name', 'Unknown')} (Tier {card_data.get('tier', '?')}) by {card_data.get('creator', 'Unknown')}")
                    
                    self.stats["cards_extracted"] += 1
                    self.stats["consecutive_errors"] = 0
                    return card_data
                else:
                    return card_data  # Return even incomplete data
                    
            except Exception as e:
                self.logger.warning(f"⚠️ Attempt {attempt + 1} failed for card {card_id}: {e}")
                self.stats["errors"] += 1
                self.stats["consecutive_errors"] += 1
                
                if attempt < self.config["retry_attempts"] - 1:
                    await asyncio.sleep(self.config["retry_delay"])
                else:
                    self.logger.error(f"❌ Failed to extract card {card_id} after all attempts")
                    return None
    
    async def _extract_meta_tags(self, page: Page) -> Dict[str, str]:
        """Extract meta tags efficiently using JavaScript evaluation."""
        try:
            meta_data = await page.evaluate("""
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
            self.logger.warning(f"⚠️ Error extracting meta tags: {e}")
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
    
    async def _extract_tier_fast(self, meta_data: Dict[str, str], html_content: str) -> str:
        """Fast tier extraction with minimal HTML parsing."""
        
        # Strategy 1: Extract from image URL (fastest and most reliable)
        og_image = meta_data.get("meta_property_og:image", "")
        if og_image:
            tier_in_url = re.search(r'/cards/([0-9S])/', og_image, re.IGNORECASE)
            if tier_in_url:
                tier = tier_in_url.group(1)
                if tier in ['1', '2', '3', '4', '5', 'S', 's']:
                    return tier.upper() if tier.lower() == 's' else tier
        
        # Strategy 2: Quick breadcrumb check (limited HTML parsing)
        breadcrumb_match = re.search(r'category=([0-9S])', html_content[:3000], re.IGNORECASE)
        if breadcrumb_match:
            tier = breadcrumb_match.group(1)
            if tier in ['1', '2', '3', '4', '5', 'S', 's']:
                return tier.upper() if tier.lower() == 's' else tier
        
        # Strategy 3: Meta tags (fallback)
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
    
    async def _extract_tier_info_accurate(self, meta_data: Dict[str, str], html_content: str, card_id: str) -> str:
        """Extract tier information using the breadcrumb method (most accurate)."""
        
        # Strategy 1: Extract from breadcrumb navigation (MOST RELIABLE)
        # Look for <ol class="breadcrumb-new"> and find category= parameter
        breadcrumb_pattern = r'<ol[^>]*class="breadcrumb-new"[^>]*>(.*?)</ol>'
        breadcrumb_match = re.search(breadcrumb_pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        if breadcrumb_match:
            breadcrumb_content = breadcrumb_match.group(1)
            # Look for category= in the breadcrumb links
            category_pattern = r'href="[^"]*[?&]category=([0-9S])[^"]*"'
            category_match = re.search(category_pattern, breadcrumb_content, re.IGNORECASE)
            
            if category_match:
                tier = category_match.group(1)
                if tier in ['1', '2', '3', '4', '5', 'S', 's']:
                    self.logger.debug(f"Found tier {tier} from breadcrumb for card {card_id}")
                    return tier.upper() if tier.lower() == 's' else tier
        
        # Strategy 2: Extract from image URL path (SECOND MOST RELIABLE)
        og_image = meta_data.get("meta_property_og:image", "")
        if og_image:
            # Image URLs contain tier info like /cards/3/ or /cards/4/
            tier_in_url = re.search(r'/cards/([0-9S])/', og_image, re.IGNORECASE)
            if tier_in_url:
                tier = tier_in_url.group(1)
                if tier in ['1', '2', '3', '4', '5', 'S', 's']:
                    self.logger.debug(f"Found tier {tier} from image URL for card {card_id}")
                    return tier.upper() if tier.lower() == 's' else tier
        
        # Strategy 3: Look in meta tags (FALLBACK)
        meta_sources = [
            meta_data.get("meta_property_og:title", ""),
            meta_data.get("page_title", ""),
            meta_data.get("meta_name_description", "")
        ]
        
        tier_patterns = [r'tier[:\s]*([0-9S]+)', r'Tier[:\s]*([0-9S]+)', r'T([0-9S])\b']
        
        for meta_text in meta_sources:
            if not meta_text:
                continue
            for pattern in tier_patterns:
                matches = re.findall(pattern, meta_text, re.IGNORECASE)
                if matches:
                    for match in matches:
                        if match in ['1', '2', '3', '4', '5', 'S', 's']:
                            self.logger.debug(f"Found tier {match} from meta tags for card {card_id}")
                            return match.upper() if match.lower() == 's' else match
        
        self.logger.warning(f"Could not determine tier for card {card_id}")
        return "Unknown"
    
    async def _extract_card_image_from_viewer(self, html_content: str, card_id: str) -> Optional[str]:
        """Extract high-resolution image from the card viewer (most accurate)."""
        
        # Look for <div class="cardData"> container (main card viewer)
        card_data_pattern = r'<div[^>]*class="cardData"[^>]*>(.*?)</div>'
        card_data_match = re.search(card_data_pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        if card_data_match:
            card_data_content = card_data_match.group(1)
            
            # Look for video (animated cards) or img (static cards)
            # Video first (animated cards)
            video_pattern = r'<video[^>]*src="([^"]+)"[^>]*>'
            video_match = re.search(video_pattern, card_data_content, re.IGNORECASE)
            if video_match:
                self.logger.debug(f"Found animated card video for {card_id}")
                return video_match.group(1)
            
            # Image (static cards)
            img_pattern = r'<img[^>]*src="([^"]+)"[^>]*>'
            img_match = re.search(img_pattern, card_data_content, re.IGNORECASE)
            if img_match:
                self.logger.debug(f"Found static card image for {card_id}")
                return img_match.group(1)
        
        return None
    
    async def _extract_owner_info(self, html_content: str, card_id: str) -> Dict[str, Any]:
        """Extract owner and issue information from the correct section."""
        
        owner_info = {
            "issue_number": "",
            "owners": []
        }
        
        # Look for <div class="padded20 user_purchased"> container
        owner_pattern = r'<div[^>]*class="padded20 user_purchased"[^>]*>(.*?)</div>'
        owner_match = re.search(owner_pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        if owner_match:
            owner_content = owner_match.group(1)
            
            # Extract issue number from small.blurple2
            issue_pattern = r'<small[^>]*class="blurple2"[^>]*>Issue #:\s*(\d+)</small>'
            issue_match = re.search(issue_pattern, owner_content, re.IGNORECASE)
            if issue_match:
                owner_info["issue_number"] = issue_match.group(1)
                self.logger.debug(f"Found issue #{issue_match.group(1)} for card {card_id}")
            
            # Extract owner names from profile pictures
            owner_pattern = r'<img[^>]*(?:alt|title)="([^"]+)"[^>]*>'
            owner_matches = re.findall(owner_pattern, owner_content, re.IGNORECASE)
            if owner_matches:
                owner_info["owners"] = owner_matches[:10]  # Limit to first 10 owners
                self.logger.debug(f"Found {len(owner_matches)} owners for card {card_id}")
        
        return owner_info
    
    async def _validate_main_card_section(self, html_content: str, card_id: str) -> str:
        """Fast validation - just truncate at first related cards section."""
        # Quick truncation at common related cards patterns
        for pattern in [r'<h[0-9][^>]*>Cards in this series', r'card-series-container', r'infinitescroll-container']:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                return html_content[:match.start()]
        
        # If no related cards section found, return first 10000 characters (main card area)
        return html_content[:10000]
    
    async def _extract_creator_info_accurate(self, meta_data: Dict[str, str], html_content: str, card_id: str) -> str:
        """Extract creator information with improved accuracy to avoid cross-contamination."""
        
        # Strategy 1: Extract from meta description (most reliable)
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
                    creator = re.sub(r'&[^;]+;', '', creator)  # Remove HTML entities
                    creator = re.sub(r'\\n.*', '', creator)    # Remove anything after newline
                    return self._clean_text(creator)
        
        # Strategy 2: Look in HTML but be more specific
        if card_id in html_content:
            # Find the section of HTML around our card ID
            card_section_match = re.search(f'{card_id}.{{0,1000}}', html_content)
            if card_section_match:
                card_section = card_section_match.group(0)
                creator_patterns = [
                    r'Card Maker:\s*([^<\n"]+)',
                    r'Creator:\s*([^<\n"]+)',
                    r'Made by:\s*([^<\n"]+)'
                ]
                
                for pattern in creator_patterns:
                    match = re.search(pattern, card_section, re.IGNORECASE)
                    if match:
                        creator = match.group(1).strip()
                        creator = re.sub(r'&[^;]+;', '', creator)
                        return self._clean_text(creator)
        
        return ""
    
    async def _extract_description_accurate(self, meta_data: Dict[str, str]) -> str:
        """Extract description with improved accuracy, prioritizing meta tags."""
        
        # Strategy 1: Meta description (most reliable)
        description = meta_data.get("meta_name_description", "")
        if description and "Here you can preview" not in description:
            return self._clean_text(description)
        
        # Strategy 2: OpenGraph description
        og_description = meta_data.get("meta_property_og:description", "")
        if og_description and og_description != description and "Here you can preview" not in og_description:
            return self._clean_text(og_description)
        
        return ""
    
    async def _extract_image_urls_enhanced(self, meta_data: Dict[str, str], card_id: str) -> Dict[str, str]:
        """Extract various image URLs using enhanced_scraper.py strategy."""
        
        image_data = {
            "image_url": "",
            "high_res_image_url": "",
            "twitter_image": "",
            "og_image": ""
        }
        
        # OpenGraph image (usually high quality)
        og_image = meta_data.get("meta_property_og:image", "")
        if og_image:
            image_data["og_image"] = og_image
            image_data["high_res_image_url"] = og_image
            image_data["image_url"] = og_image
        
        # Twitter image
        twitter_image = meta_data.get("meta_name_twitter:image", "")
        if twitter_image:
            image_data["twitter_image"] = twitter_image
            if not image_data["image_url"]:
                image_data["image_url"] = twitter_image
        
        # API endpoint (fallback)
        if not image_data["image_url"] and card_id:
            api_url = f"https://api.shoob.gg/site/api/cardr/{card_id}?size=700"
            image_data["image_url"] = api_url
        
        return image_data
    
    async def _extract_creator_info_enhanced(self, html_content: str) -> str:
        """Extract card creator/maker information using enhanced_scraper.py strategy."""
        
        creator_patterns = [
            r'Card Maker:\s*([^\\n<"]+)',
            r'Creator:\s*([^\\n<"]+)',
            r'Made by:\s*([^\\n<"]+)',
            r'Artist:\s*([^\\n<"]+)',
        ]
        
        for pattern in creator_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                creator = match.group(1).strip()
                # Clean up any HTML entities or extra text
                creator = re.sub(r'&[^;]+;', '', creator)
                return self._clean_text(creator)
        
        return ""
    
    async def _extract_date_info_enhanced(self, meta_data: Dict[str, str], html_content: str) -> Dict[str, str]:
        """Extract date information using enhanced_scraper.py strategy."""
        
        date_data = {
            "creation_date": "",
            "last_updated": ""
        }
        
        # Last updated from meta
        updated_time = meta_data.get("meta_property_og:updated_time", "")
        if updated_time:
            date_data["last_updated"] = updated_time
        
        # Look for creation dates in HTML
        date_patterns = [
            r'created[:\s]*(\d{4}-\d{2}-\d{2})',
            r'date[:\s]*(\d{4}-\d{2}-\d{2})',
            r'(\d{1,2}/\d{1,2}/\d{4})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                date_data["creation_date"] = match.group(1)
                break
        
        return date_data
    
    async def _extract_description_enhanced(self, meta_data: Dict[str, str], html_content: str) -> str:
        """Extract card description using enhanced_scraper.py strategy."""
        
        # Use meta description as primary source
        description = meta_data.get("meta_name_description", "")
        if description and description != "Here you can preview given card, see the entire collection and people who own it.":
            return self._clean_text(description)
        
        # Try OpenGraph description
        og_description = meta_data.get("meta_property_og:description", "")
        if og_description and og_description != description:
            return self._clean_text(og_description)
        
        return ""
    
    async def _extract_additional_metadata_enhanced(self, html_content: str) -> Dict[str, Any]:
        """Extract additional metadata like rarity, stats, etc. using enhanced_scraper.py strategy."""
        
        additional_data = {}
        
        # Look for rarity information
        rarity_patterns = [
            r'rarity[:\s]*([^\\n<"]+)',
            r'rare[:\s]*([^\\n<"]+)',
        ]
        
        for pattern in rarity_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                additional_data["rarity"] = self._clean_text(match.group(1))
                break
        
        # Look for stats (attack, defense, HP, etc.)
        stats = {}
        stat_patterns = [
            (r'attack[:\s]*(\d+)', 'attack'),
            (r'defense[:\s]*(\d+)', 'defense'),
            (r'hp[:\s]*(\d+)', 'hp'),
            (r'power[:\s]*(\d+)', 'power'),
        ]
        
        for pattern, stat_name in stat_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                stats[stat_name] = int(match.group(1))
        
        if stats:
            additional_data["stats"] = stats
        
        # Look for tags or categories
        tag_patterns = [
            r'tags?[:\s]*\[([^\]]+)\]',
            r'categories?[:\s]*\[([^\]]+)\]',
        ]
        
        for pattern in tag_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                tags = [tag.strip().strip('"\'') for tag in match.group(1).split(',')]
                additional_data["tags"] = tags
                break
        
        return additional_data
    
    def _validate_card_data_enhanced(self, card_data: Dict[str, Any]) -> bool:
        """Validate if card data is complete enough to be useful using enhanced_scraper.py strategy."""
        return (
            card_data.get("name", "") not in ["", "Unknown Card", "Card preview"] and
            card_data.get("image_url", "") != ""
        )
    
    async def _scrape_page(self, page: Page, page_num: int) -> List[Dict[str, Any]]:
        """Scrape all cards from a single page."""
        self.logger.info(f"🚀 Scraping page {page_num}")
        
        try:
            # Get card links from the page
            card_links = await self._get_card_links_from_page(page, page_num)
            
            if not card_links:
                self.logger.warning(f"⚠️ No cards found on page {page_num}")
                return []
            
            # Extract data from each card
            page_cards = []
            
            for i, card_url in enumerate(card_links):
                try:
                    card_data = await self._extract_card_data(page, card_url)
                    if card_data:
                        page_cards.append(card_data)
                    
                    # Respectful delay between cards
                    if i < len(card_links) - 1:
                        await asyncio.sleep(self.config["card_delay"])
                        
                except Exception as e:
                    self.logger.error(f"❌ Error processing card {i+1}/{len(card_links)}: {e}")
                    self.stats["errors"] += 1
                    continue
            
            self.logger.info(f"✅ Page {page_num}: Extracted {len(page_cards)}/{len(card_links)} cards")
            self.stats["pages_scraped"] += 1
            
            # Add cards to main collection
            self.all_cards.extend(page_cards)
            self.scraped_pages.add(page_num)
            
            # Save progress periodically
            self._save_progress()
            
            return page_cards
            
        except Exception as e:
            self.logger.error(f"❌ Error scraping page {page_num}: {e}")
            self.stats["errors"] += 1
            return []
    
    def _calculate_statistics(self) -> Dict[str, Any]:
        """Calculate comprehensive scraping statistics."""
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
            "average_cards_per_page": round(self.stats["cards_extracted"] / max(self.stats["pages_scraped"], 1), 1)
        }
    
    def _save_final_output(self) -> Path:
        """Save all cards to a single output file."""
        output_file = OUTPUT_DIR / self.config["output_file"]
        
        try:
            # Calculate final statistics
            final_stats = self._calculate_statistics()
            
            # Create comprehensive output data
            output_data = {
                "scrape_info": {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "scraper_version": SCRAPER_VERSION,
                    "total_cards": len(self.all_cards),
                    "source": self.urls["base_url"],
                    "method": "comprehensive_individual_card_extraction",
                    "session_statistics": final_stats,
                    "configuration": {
                        "pages_range": f"{self.config['start_page']}-{self.config.get('end_page', 'auto')}",
                        "page_delay": self.config["page_delay"],
                        "card_delay": self.config["card_delay"],
                        "include_metadata": self.config["include_metadata"],
                        "resume_enabled": self.config["enable_resume"]
                    },
                    "data_fields": [
                        "card_id", "card_url", "name", "tier", "character_source", 
                        "series", "image_url", "high_res_image_url", "creator", 
                        "card_maker", "description", "last_updated", "extraction_timestamp"
                    ]
                },
                "cards": self.all_cards
            }
            
            # Write to file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(
                    output_data,
                    f,
                    ensure_ascii=False,
                    indent=2 if self.config["pretty_print"] else None,
                    sort_keys=True
                )
            
            self.logger.info(f"💾 Final output saved to: {output_file}")
            self.logger.info(f"📊 Total cards in file: {len(self.all_cards)}")
            
            return output_file
            
        except Exception as e:
            self.logger.error(f"❌ Error saving final output: {e}")
            raise
    
    async def scrape_all_pages(self, start_page: Optional[int] = None, end_page: Optional[int] = None) -> Dict[str, Any]:
        """
        Main scraping method with professional error handling and progress tracking.
        
        Args:
            start_page: Starting page number (overrides config)
            end_page: Ending page number (overrides config)
            
        Returns:
            Dictionary containing comprehensive scraping statistics
        """
        # Initialize
        self.stats["start_time"] = time.time()
        start_page = start_page or self.config["start_page"]
        end_page = end_page or self.config["end_page"]
        
        # Load previous progress
        self._load_progress()
        
        # Setup browser
        browser, context, page = await self._setup_browser()
        
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
            
            self.logger.info(f"📊 Scraping Plan:")
            self.logger.info(f"   Pages range: {start_page} to {end_page}")
            self.logger.info(f"   Pages to scrape: {len(pages_to_scrape)}")
            self.logger.info(f"   Pages to skip: {len(self.scraped_pages)}")
            
            # Check for consecutive errors
            consecutive_error_limit = ERROR_CONFIG["max_consecutive_errors"]
            
            # Scrape pages
            for page_num in pages_to_scrape:
                try:
                    # Check consecutive error limit
                    if self.stats["consecutive_errors"] >= consecutive_error_limit:
                        self.logger.error(f"❌ Too many consecutive errors ({consecutive_error_limit}), stopping")
                        break
                    
                    # Scrape the page
                    await self._scrape_page(page, page_num)
                    
                    # Progress update
                    if LOGGING_CONFIG["show_progress"]:
                        progress = (len(self.scraped_pages) / len(pages_to_scrape)) * 100
                        self.logger.info(f"📈 Progress: {progress:.1f}% ({len(self.scraped_pages)}/{len(pages_to_scrape)} pages)")
                    
                    # Respectful delay between pages
                    if page_num < max(pages_to_scrape):
                        await asyncio.sleep(self.config["page_delay"])
                    
                except Exception as e:
                    self.logger.error(f"❌ Critical error processing page {page_num}: {e}")
                    self.stats["errors"] += 1
                    self.stats["consecutive_errors"] += 1
                    
                    if ERROR_CONFIG["continue_on_error"]:
                        await asyncio.sleep(ERROR_CONFIG["error_cooldown"])
                        continue
                    else:
                        break
            
            # Calculate and display final statistics
            final_stats = self._calculate_statistics()
            
            if LOGGING_CONFIG["show_statistics"]:
                self.logger.info("🎉 Scraping completed!")
                self.logger.info(f"📊 Final Statistics:")
                self.logger.info(f"   Pages scraped: {final_stats['pages_scraped']}")
                self.logger.info(f"   Pages skipped: {final_stats['pages_skipped']}")
                self.logger.info(f"   Cards extracted: {final_stats['cards_extracted']}")
                self.logger.info(f"   Success rate: {final_stats['success_rate']}%")
                self.logger.info(f"   Total time: {final_stats['elapsed_time']}s")
                self.logger.info(f"   Speed: {final_stats['cards_per_second']} cards/sec")
                self.logger.info(f"   Average: {final_stats['average_cards_per_page']} cards/page")
            
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
            await context.close()
            await browser.close()
    
    def get_scraped_data_summary(self) -> Dict[str, Any]:
        """Get a summary of scraped data."""
        output_file = OUTPUT_DIR / self.config["output_file"]
        
        summary = {
            "total_cards": len(self.all_cards),
            "scraped_pages": sorted(list(self.scraped_pages)),
            "output_file": str(output_file) if output_file.exists() else None,
            "session_id": self.session_id,
            "last_updated": datetime.now(timezone.utc).isoformat()
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
                self.logger.warning(f"⚠️ Error getting file info: {e}")
        
        return summary