"""
Advanced Event-Driven Shoob.gg Card Scraper Configuration
========================================================

Smart-waiting configuration for event-driven scraping.
No fixed delays - waits for actual data loading events.
"""

import logging

# ============================================================================
# SCRAPING CONFIGURATION
# ============================================================================

SCRAPING_CONFIG = {
    # Page range settings
    "start_page": 1,
    "end_page": 2311,
    
    # Smart waiting (no fixed delays - event-driven)
    "max_wait_timeout": 30000,     # Maximum wait for any element (30s)
    "card_load_timeout": 15000,    # Wait for cards to load (15s)
    "page_load_timeout": 20000,    # Wait for page navigation (20s)
    "element_check_interval": 100, # Check interval for elements (100ms)
    
    # Minimal delays (only when absolutely necessary)
    "minimal_delay": 0.1,          # Tiny delay for DOM stabilization
    "network_settle_time": 0.5,    # Wait for network to settle after navigation
    
    # Output settings
    "output_file": "shoob_cards_advanced.json",
    "output_folder": "output",
    "pretty_print": True,
    "include_metadata": True,
    "live_save": True,
    
    # Resume functionality
    "enable_resume": True,
    "resume_file": "scraping_progress_advanced.json",
    
    # Performance settings
    "retry_attempts": 3,
    "retry_delay": 1.0,
}

# ============================================================================
# BROWSER CONFIGURATION
# ============================================================================

BROWSER_CONFIG = {
    # Browser launch settings
    "headless": True,
    "user_agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "viewport": {"width": 1920, "height": 1080},
    "locale": "en-US",
    "timezone": "America/New_York",
    
    # Anti-detection measures
    "browser_args": [
        "--no-sandbox",
        "--disable-blink-features=AutomationControlled",
        "--disable-dev-shm-usage",
        "--disable-web-security",
        "--disable-features=VizDisplayCompositor",
    ],
    
    # Additional headers
    "extra_headers": {
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
    }
}

# ============================================================================
# SMART WAITING SELECTORS
# ============================================================================

WAIT_SELECTORS = {
    # Page-level selectors (wait for these to confirm page is loaded)
    "cards_container": "a[href*='/cards/info/']",  # Wait for card links to appear
    "cards_loaded": "a[href*='/cards/info/']:nth-child(5)",  # Wait for at least 5 cards (more realistic)
    "page_content": ".container, .content, main, body",  # Wait for main content
    
    # Card detail page selectors (more flexible)
    "card_title": "meta[property='og:title'], title",  # Wait for any title
    "card_meta": "meta[property='og:image'], meta[name='description']",  # Wait for any meta
    "card_content": ".card-main, .cardData, .card-info, main, body",  # Wait for any content
    "breadcrumb": ".breadcrumb-new, .breadcrumb, nav",  # Wait for navigation
    
    # Data-specific selectors (more lenient)
    "basic_meta": "meta[property='og:title'], meta[name='description'], title",
    "any_image": "meta[property='og:image'], meta[name='twitter:image'], img",
    "page_loaded": "head, body",  # Basic page structure
}

# ============================================================================
# URL CONFIGURATION
# ============================================================================

URLS = {
    "base_url": "https://shoob.gg/cards",
    "site_url": "https://shoob.gg",
    "cdn_base": "https://cdn.shoob.gg",
    "api_base": "https://api.shoob.gg/site/api",
}

# ============================================================================
# DATA EXTRACTION CONFIGURATION
# ============================================================================

DATA_CONFIG = {
    # Default values for missing fields
    "default_values": {
        "name": "Unknown Card",
        "tier": "Unknown",
        "character_source": "Unknown Series",
        "image_url": "",
        "creator": "",
        "description": "",
    },
    
    # Text processing settings
    "clean_text": True,
    "remove_extra_whitespace": True,
    "max_field_length": {
        "name": 100,
        "description": 500,
        "creator": 50,
    },
    
    # Image URL preferences
    "prefer_high_res": True,
    "image_size_preference": "700",
    
    # Data validation
    "validate_required_fields": ["name", "card_id", "image_url"],
    "skip_invalid_cards": False,
}

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOGGING_CONFIG = {
    # Logging levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
    "level": logging.INFO,
    "format": "%(asctime)s | %(levelname)-7s | %(message)s",
    "date_format": "%H:%M:%S",
    
    # Console output settings
    "show_progress": True,
    "show_card_details": False,     # Disabled for clean output
    "show_wait_times": False,       # Disabled for clean output
    "show_statistics": True,
    "use_colors": True,
    
    # File logging for errors
    "log_to_file": True,
    "log_file": "scraper_errors.log",
    "max_log_size_mb": 10,
    "backup_count": 3,
}

# ============================================================================
# SELECTOR CONFIGURATION
# ============================================================================

SELECTORS = {
    # Card link selectors (for finding individual card pages)
    "card_links": [
        "a[href*='/cards/info/']",
        "a[href*='/inventory/']",
    ],
    
    # Meta tag selectors for data extraction
    "meta_selectors": {
        "title": ["meta[property='og:title']", "title"],
        "description": ["meta[name='description']", "meta[property='og:description']"],
        "image": ["meta[property='og:image']", "meta[name='twitter:image']"],
        "updated": ["meta[property='og:updated_time']"],
    }
}

# ============================================================================
# ERROR HANDLING CONFIGURATION
# ============================================================================

ERROR_CONFIG = {
    # Error handling behavior
    "continue_on_error": True,
    "max_consecutive_errors": 5,
    "error_cooldown": 2.0,
    
    # Specific error handling
    "timeout_retry": True,
    "network_error_retry": True,
    "page_not_found_skip": True,
    
    # Debug settings
    "save_error_screenshots": False,
    "save_error_html": False,
    "error_output_folder": "errors",
}

# ============================================================================
# PERFORMANCE MONITORING
# ============================================================================

PERFORMANCE_CONFIG = {
    # Statistics tracking
    "track_performance": True,
    "show_speed_stats": True,
    "track_wait_times": True,
    "memory_monitoring": True,
    
    # Performance thresholds
    "slow_page_threshold": 10.0,
    "memory_warning_threshold": 400,
    
    # Smart waiting optimization
    "adaptive_timeouts": True,
    "learn_from_patterns": True,
}

# ============================================================================
# VALIDATION AND CONSTANTS
# ============================================================================

# File paths
from pathlib import Path
OUTPUT_DIR = Path(SCRAPING_CONFIG["output_folder"])
LOG_DIR = Path("logs")

# Validation
REQUIRED_FIELDS = DATA_CONFIG["validate_required_fields"]
MAX_PAGES_PER_SESSION = 1000

# Version info
SCRAPER_VERSION = "1.0.0-advanced"
CONFIG_VERSION = "1.0.0"
LAST_UPDATED = "2025-12-26"

# ============================================================================
# RUNTIME CONFIGURATION VALIDATION
# ============================================================================

def validate_config():
    """Validate configuration settings."""
    errors = []
    
    # Check required directories
    try:
        OUTPUT_DIR.mkdir(exist_ok=True)
        LOG_DIR.mkdir(exist_ok=True)
    except Exception as e:
        errors.append(f"Cannot create directories: {e}")
    
    # Validate page range
    if (SCRAPING_CONFIG["end_page"] is not None and 
        SCRAPING_CONFIG["start_page"] > SCRAPING_CONFIG["end_page"]):
        errors.append("start_page cannot be greater than end_page")
    
    # Validate timeouts
    if SCRAPING_CONFIG["max_wait_timeout"] < 5000:
        errors.append("max_wait_timeout should be at least 5 seconds")
    
    if errors:
        raise ValueError(f"Configuration errors: {'; '.join(errors)}")

# Auto-validate on import
validate_config()
