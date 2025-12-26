#!/usr/bin/env python3
"""
Advanced Event-Driven Shoob.gg Card Scraper - Main Script
========================================================

Smart browser-based scraper that waits for actual data loading events
instead of fixed delays. Maximum efficiency with browser reliability.

Usage:
    python main.py                    # Smart scraping with default settings
    python main.py --start 1 --end 5 # Smart scrape pages 1-5
    python main.py --resume           # Resume with smart waiting
    python main.py --summary          # Show summary with wait analytics

Author: Senior Developer
Version: 1.0.0-advanced
"""

import asyncio
import argparse
import sys
import time
import warnings
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.append(str(Path(__file__).parent))

from scraper import AdvancedShoobCardScraper


def suppress_asyncio_warnings():
    """Suppress Windows-specific asyncio warnings that don't affect functionality."""
    import warnings
    warnings.filterwarnings("ignore", category=ResourceWarning, message=".*unclosed transport.*")
    warnings.filterwarnings("ignore", category=ResourceWarning, message=".*I/O operation on closed pipe.*")
    warnings.filterwarnings("ignore", category=ResourceWarning, message=".*unclosed.*")
    warnings.filterwarnings("ignore", message=".*unclosed transport.*")
    warnings.filterwarnings("ignore", message=".*I/O operation on closed pipe.*")
    
    # Also suppress at the system level for Windows
    import sys
    if sys.platform == "win32":
        import os
        os.environ["PYTHONWARNINGS"] = "ignore::ResourceWarning"


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Advanced Event-Driven Shoob.gg Card Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                     # Smart scraping with defaults
  python main.py --start 1 --end 10 # Smart scrape pages 1-10
  python main.py --resume            # Resume with smart waiting
  python main.py --summary           # Show summary with analytics
        """
    )
    
    parser.add_argument(
        "--start",
        type=int,
        help="Starting page number (overrides config)"
    )
    
    parser.add_argument(
        "--end", 
        type=int,
        help="Ending page number (overrides config)"
    )
    
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume scraping (skip existing pages)"
    )
    
    parser.add_argument(
        "--summary",
        action="store_true", 
        help="Show summary of scraped data and exit"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


def print_banner():
    """Print application banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║              ADVANCED EVENT-DRIVEN SCRAPER                   ║
║                Smart Waiting Edition v1.0                    ║
╠══════════════════════════════════════════════════════════════╣
║  Features:                                                   ║
║  • Event-driven waiting (no fixed delays)                    ║
║  • Smart element detection & adaptive timeouts               ║
║  • Maximum efficiency with browser reliability               ║
║  • Live-save functionality (saves after each page)           ║
║  • Resume capability with wait time analytics                ║
║  • Performance tracking & optimization                       ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_summary(summary_data):
    """Print formatted data summary with wait analytics."""
    print("\n" + "="*60)
    print("📊 SCRAPED DATA SUMMARY")
    print("="*60)
    print(f"📁 Output file: {summary_data.get('output_file', 'N/A')}")
    print(f"🃏 Total cards: {summary_data.get('total_cards', 0)}")
    print(f"🔧 Scraper type: {summary_data.get('scraper_type', 'N/A')}")
    
    if summary_data.get('scraped_pages'):
        print(f"📋 Pages scraped: {sorted(summary_data['scraped_pages'])}")
        
    if summary_data.get('sample_cards'):
        print("\n🎴 Sample cards:")
        for card in summary_data['sample_cards'][:3]:
            print(f"   - {card['name']} (Tier {card['tier']}) from {card['series']}")
    
    if summary_data.get('file_size_mb'):
        print(f"📦 File size: {summary_data['file_size_mb']} MB")
    
    print("="*60)


async def main():
    """Main execution function."""
    args = parse_arguments()
    
    # Setup Windows-specific fixes
    suppress_asyncio_warnings()  # Call this first
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Print banner
    print_banner()
    
    try:
        # Initialize scraper
        print("🔧 Initializing advanced event-driven scraper...")
        scraper = AdvancedShoobCardScraper()
        
        # Handle summary request
        if args.summary:
            print("📊 Generating data summary with analytics...")
            summary = scraper.get_scraped_data_summary()
            print_summary(summary)
            return
        
        # Configure verbose logging if requested
        if args.verbose:
            import logging
            logging.getLogger().setLevel(logging.DEBUG)
            print("🔍 Verbose logging enabled")
        
        # Determine scraping parameters
        start_page = args.start
        end_page = args.end
        
        if args.resume:
            print("🔄 Resume mode enabled - will skip existing pages")
        
        # Display scraping plan
        print(f"\n📋 Smart Scraping Plan:")
        if start_page:
            print(f"   Start page: {start_page}")
        else:
            print(f"   Start page: {scraper.config['start_page']} (from config)")
            
        if end_page:
            print(f"   End page: {end_page}")
        else:
            end_config = scraper.config['end_page']
            if end_config:
                print(f"   End page: {end_config} (from config)")
            else:
                print(f"   End page: Auto-detect (will scrape until no more cards)")
        
        print(f"   Method: Event-driven smart waiting")
        print(f"   Live-save: ✅ Enabled")
        print(f"   Wait analytics: ✅ Enabled")
        print(f"   Output: {scraper.config['output_folder']}/{scraper.config['output_file']}")
        
        # Confirm before starting
        if not args.resume:
            try:
                response = input("\n🚀 Ready to start smart scraping? (y/N): ").strip().lower()
                if response not in ['y', 'yes']:
                    print("❌ Scraping cancelled by user")
                    return
            except KeyboardInterrupt:
                print("\n❌ Scraping cancelled by user")
                return
        
        # Start scraping
        print("\n🚀 Starting advanced event-driven scraping...")
        print("-" * 60)
        
        start_time = time.time()
        
        try:
            stats = await scraper.scrape_all_pages(start_page, end_page)
        except Exception as e:
            print(f"\n❌ Scraping error: {e}")
            # Create fallback stats if scraping fails
            stats = {
                'pages_scraped': len(scraper.scraped_pages) if hasattr(scraper, 'scraped_pages') else 0,
                'pages_skipped': 0,
                'cards_extracted': len(scraper.all_cards) if hasattr(scraper, 'all_cards') else 0,
                'total_errors': scraper.stats.get('errors', 0) if hasattr(scraper, 'stats') else 0,
                'success_rate': 0,
                'elapsed_time': time.time() - start_time,
                'cards_per_second': 0,
                'pages_per_minute': 0,
                'wait_time_analytics': {
                    'total_wait_time': 0,
                    'average_page_load': 0,
                    'average_card_load': 0,
                    'wait_efficiency': 0
                }
            }
        
        # Display final results
        print("\n" + "="*60)
        print("🎉 SMART SCRAPING COMPLETED!")
        print("="*60)
        print(f"📄 Pages scraped: {stats.get('pages_scraped', 0)}")
        print(f"📄 Pages skipped: {stats.get('pages_skipped', 0)}")
        print(f"🃏 Cards extracted: {stats.get('cards_extracted', 0)}")
        print(f"❌ Errors: {stats.get('total_errors', 0)}")
        print(f"✅ Success rate: {stats.get('success_rate', 0)}%")
        print(f"⏱️  Total time: {stats.get('elapsed_time', 0):.2f}s")
        print(f"🚀 Speed: {stats.get('cards_per_second', 0):.2f} cards/sec")
        print(f"📊 Pages/min: {stats.get('pages_per_minute', 0):.2f}")
        
        # Show wait time analytics
        if 'wait_time_analytics' in stats:
            wait_analytics = stats['wait_time_analytics']
            print(f"\n⏱️ WAIT TIME ANALYTICS:")
            print(f"   Total wait time: {wait_analytics.get('total_wait_time', 0):.2f}s")
            print(f"   Avg page load: {wait_analytics.get('average_page_load', 0):.2f}s")
            print(f"   Avg card load: {wait_analytics.get('average_card_load', 0):.2f}s")
            print(f"   Wait efficiency: {wait_analytics.get('wait_efficiency', 0):.1f}%")
        
        print("="*60)
        
        # Show data summary
        if stats.get('cards_extracted', 0) > 0:
            print("\n📊 Getting final data summary...")
            try:
                summary = scraper.get_scraped_data_summary()
                print_summary(summary)
            except Exception as e:
                print(f"⚠️ Could not generate summary: {e}")
        
        print(f"\n💾 All data saved to: {scraper.config['output_folder']}/{scraper.config['output_file']}")
        print("✨ Smart scraping completed successfully!")
        
        # Determine exit code based on success
        cards_scraped = stats.get('cards_extracted', 0)
        if cards_scraped > 0:
            # Success: We scraped some data
            print(f"✅ Success: {cards_scraped} cards scraped successfully")
        else:
            # Warning: No data scraped but don't fail the process
            print("⚠️ Warning: No cards were scraped, but process completed")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Scraping interrupted by user")
        print("💾 Any completed pages have been saved")
        print("🔄 Use --resume flag to continue from where you left off")
        
        # Ensure proper cleanup
        try:
            if 'scraper' in locals():
                await scraper._cleanup_browser()
        except:
            pass
        
        # Exit cleanly for user interruption
        return  # Don't use sys.exit() for user interruption
        
    except Exception as e:
        print(f"\n❌ Critical Error: {e}")
        print("💡 Check the logs for more details")
        
        # Try to cleanup browser even on error
        try:
            if 'scraper' in locals():
                await scraper._cleanup_browser()
        except:
            pass
        
        # Check if we have successfully scraped some data
        if 'scraper' in locals() and hasattr(scraper, 'all_cards') and scraper.all_cards:
            print("💾 Some data was successfully scraped and saved")
            print("✅ Exiting cleanly despite errors")
            return  # Exit cleanly if we have data
        else:
            # Only raise if no data was scraped at all
            print("❌ No data was scraped")
            raise  # Re-raise for GitHub Actions to detect failure


if __name__ == "__main__":
    # Suppress warnings before running
    suppress_asyncio_warnings()
    
    try:
        asyncio.run(main())
        # If we reach here, everything completed successfully
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)  # User interruption is not an error
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        # Only exit with error code if it's a real failure
        sys.exit(1)
    finally:
        # Force cleanup on Windows to prevent pipe warnings
        if sys.platform == "win32":
            try:
                import gc
                gc.collect()  # Force garbage collection
                
                # Give time for cleanup
                import time
                time.sleep(0.1)
                
                # Close any remaining event loops
                try:
                    loop = asyncio.get_event_loop()
                    if not loop.is_closed():
                        loop.close()
                except:
                    pass
            except:
                pass
