"""
Professional Shoob.gg Card Scraper Configuration
===============================================

Configuration settings for the professional-grade Shoob.gg card scraper.
Adjust these settings to customize scraper behavior.

Author: Senior Developer
Version: 2.0.0
"""

import logging
from pathlib import Path

# ============================================================================
# SCRAPING CONFIGURATION
# ============================================================================

SCRAPING_CONFIG = {
    # Page range settings
    "start_page": 1,
    "end_page": 10,  # Set to None for unlimited scraping
    
    # Timing and delays (seconds) - optimized for speed
    "page_delay": 1.5,          # Delay between pages (reduced)
    "card_delay": 0.8,          # Delay between individual cards (reduced)
    "timeout": 25000,           # Page load timeout (reduced to 25s)
    "retry_attempts": 2,        # Number of retry attempts (reduced)
    "retry_delay": 3.0,         # Delay between retries (reduced)
    
    # Output settings
    "output_file": "shoob_cards.json",
    "output_folder": "output",
    "save_mode": "single_file",  # "single_file" or "per_page"
    "pretty_print": True,
    "include_metadata": True,   # Include raw meta tags (like enhanced_scraper)
    
    # Resume functionality
    "enable_resume": True,
    "resume_file": "scraping_progress.json",
    
    # Performance settings
    "max_concurrent_cards": 1,  # Process cards sequentially for stability
    "memory_limit_mb": 500,     # Memory usage limit
}

# ============================================================================
# BROWSER CONFIGURATION
# ============================================================================

BROWSER_CONFIG = {
    # Browser launch settings
    "headless": True,           # Set to False to see browser window
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
    "image_size_preference": "700",  # For API fallback URLs
    
    # Data validation
    "validate_required_fields": ["name", "card_id", "image_url"],
    "skip_invalid_cards": False,  # Include incomplete cards in output
}

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOGGING_CONFIG = {
    # Logging levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
    "level": logging.INFO,
    "format": "%(asctime)s | %(levelname)-7s | %(message)s",
    "date_format": "%H:%M:%S",
    
    # File logging (optional)
    "log_to_file": False,
    "log_file": "scraper.log",
    "max_log_size_mb": 10,
    "backup_count": 3,
    
    # Console output settings
    "show_progress": True,
    "show_card_details": False,  # Disabled for speed - set to True for debugging
    "show_statistics": True,
    "use_colors": True,
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
    "error_cooldown": 10.0,  # Seconds to wait after consecutive errors
    
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
    "memory_monitoring": True,
    
    # Performance thresholds
    "slow_page_threshold": 10.0,  # Seconds
    "memory_warning_threshold": 400,  # MB
    
    # Auto-optimization
    "auto_adjust_delays": False,  # Experimental feature
    "adaptive_timeout": False,    # Experimental feature
}

# ============================================================================
# VALIDATION AND CONSTANTS
# ============================================================================

# File paths
OUTPUT_DIR = Path(SCRAPING_CONFIG["output_folder"])
LOG_DIR = Path("logs")

# Validation
REQUIRED_FIELDS = DATA_CONFIG["validate_required_fields"]
MAX_PAGES_PER_SESSION = 1000  # Safety limit

# Version info
SCRAPER_VERSION = "2.0.0"
CONFIG_VERSION = "2.0.0"
LAST_UPDATED = "2025-12-25"

# ============================================================================
# RUNTIME CONFIGURATION VALIDATION
# ============================================================================

def validate_config():
    """Validate configuration settings."""
    errors = []
    
    # Check required directories
    try:
        OUTPUT_DIR.mkdir(exist_ok=True)
        if LOGGING_CONFIG["log_to_file"]:
            LOG_DIR.mkdir(exist_ok=True)
    except Exception as e:
        errors.append(f"Cannot create directories: {e}")
    
    # Validate page range
    if (SCRAPING_CONFIG["end_page"] is not None and 
        SCRAPING_CONFIG["start_page"] > SCRAPING_CONFIG["end_page"]):
        errors.append("start_page cannot be greater than end_page")
    
    # Validate delays
    if SCRAPING_CONFIG["page_delay"] < 0.5:
        errors.append("page_delay should be at least 0.5 seconds")
    
    if errors:
        raise ValueError(f"Configuration errors: {'; '.join(errors)}")

# Auto-validate on import
validate_config()