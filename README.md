# Advanced Event-Driven Shoob.gg Card Scraper

Professional browser-based scraper with smart waiting technology. Waits for actual data loading events instead of fixed delays.

## Features

- **Event-Driven Waiting**: Waits for DOM elements instead of fixed timers
- **Smart Element Detection**: Detects when cards and data are fully loaded  
- **Adaptive Timeouts**: Adjusts waiting based on actual loading patterns
- **Live-Save Functionality**: Saves progress after each page
- **Resume Capability**: Continue from where you left off
- **Performance Analytics**: Tracks wait times and efficiency metrics
- **Clean Progress Display**: Professional progress indicators
- **Error Logging**: Comprehensive error tracking to files

## Installation

```bash
cd advance1
pip install -r requirements.txt
playwright install chromium
```

## Usage

### Basic Usage
```bash
python main.py                    # Smart scraping with defaults
python main.py --start 1 --end 5 # Scrape pages 1-5
python main.py --resume           # Resume previous session
python main.py --summary          # Show data summary
```

### Advanced Options
```bash
python main.py --verbose          # Enable detailed logging
```

## Configuration

Edit `config.py` to customize scraping behavior:

```python
SCRAPING_CONFIG = {
    "start_page": 1,
    "end_page": 10,
    "max_wait_timeout": 30000,     # Maximum wait time (30s)
    "card_load_timeout": 15000,    # Card loading timeout (15s)
    "live_save": True,             # Save after each page
    "enable_resume": True,         # Resume capability
}
```

## Output

Data is saved to `output/shoob_cards_advanced.json` with comprehensive metadata:

```json
{
  "scrape_info": {
    "timestamp": "2025-12-26T15:44:24Z",
    "scraper_version": "1.0.0-advanced",
    "scraper_type": "advanced_event_driven",
    "total_cards": 150,
    "session_statistics": {
      "pages_scraped": 10,
      "success_rate": 100.0,
      "elapsed_time": 120.5,
      "cards_per_second": 1.24,
      "wait_time_analytics": {
        "total_wait_time": 45.2,
        "average_page_load": 2.1,
        "wait_efficiency": 62.5
      }
    }
  },
  "cards": [...]
}
```

## Project Structure

```
advance1/
├── main.py              # Main execution script
├── scraper.py           # Event-driven scraper class
├── config.py            # Configuration settings
├── requirements.txt     # Dependencies
├── README.md           # Documentation
├── logs/               # Error logs
└── output/             # Scraped data
```

## How Smart Waiting Works

### Traditional Approach
```python
await page.goto(url)
await asyncio.sleep(5)  # Always wait 5 seconds
```

### Event-Driven Approach
```python
await page.goto(url)
await page.wait_for_selector("cards_loaded")  # Wait until ready
```

## Performance Benefits

| Aspect | Fixed Delays | Smart Waiting |
|--------|-------------|---------------|
| Speed | Wastes time on fast pages | Adapts to loading speed |
| Reliability | May miss slow data | Waits until data ready |
| Efficiency | Fixed overhead | Optimized waiting |

## Troubleshooting

### Common Issues

**Timeout Errors**: Increase `max_wait_timeout` in config.py
**Missing Cards**: Check `card_load_timeout` setting
**Slow Performance**: Enable `--verbose` to see wait analytics

### Debug Mode
```bash
python main.py --verbose  # See detailed wait times
```

## Error Handling

- All errors are logged to `logs/scraper_errors.log`
- Console output remains clean during operation
- Failed cards are tracked and can be retried
- Automatic recovery from network issues

## Resume Functionality

The scraper automatically saves progress and can resume:
- Progress saved after each page
- Skip already scraped pages on resume
- Maintain data integrity across sessions

---

**Version**: 1.0.0-advanced  
**Type**: Event-Driven Browser Scraper  
**Dependencies**: Playwright, Python 3.8+
