#!/usr/bin/env python3
"""
GitHub Actions Helper Script
============================

This script handles JSON file verification and output generation
for the GitHub Actions workflow, avoiding Python-in-YAML issues.
"""

import json
import sys
import os
from pathlib import Path


def verify_output_files():
    """Verify output files and generate GitHub Actions outputs."""
    
    # Check if required files exist
    data_file = Path("output/data.json")
    process_file = Path("output/process.json")
    
    if not data_file.exists() or not process_file.exists():
        print("❌ Required output files missing")
        if data_file.exists():
            print("✅ data.json exists")
        else:
            print("❌ data.json missing")
            
        if process_file.exists():
            print("✅ process.json exists")
        else:
            print("❌ process.json missing")
            
        # List what's actually in output directory
        output_dir = Path("output")
        if output_dir.exists():
            print(f"📁 Contents of output/:")
            for file in output_dir.iterdir():
                print(f"   - {file.name}")
        else:
            print("📁 output/ directory doesn't exist")
            
        return False
    
    try:
        # Read data.json
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        card_count = data.get('total', 0)
        
        # Read process.json
        with open(process_file, 'r', encoding='utf-8') as f:
            process = json.load(f)
        
        completed_pages = len(process.get('scraped_pages', []))
        total_cards_in_process = process.get('total_cards', 0)
        
        # Output for GitHub Actions (append to GITHUB_OUTPUT)
        github_output = os.environ.get('GITHUB_OUTPUT')
        if github_output:
            with open(github_output, 'a') as f:
                f.write(f"card_count={card_count}\n")
                f.write(f"completed_pages={completed_pages}\n")
        
        # Console output for logs
        print("✅ Output files verified")
        print(f"📊 Total cards: {card_count}")
        print(f"📄 Completed pages: {completed_pages}")
        print(f"🔄 Cards in process file: {total_cards_in_process}")
        
        # Verify data consistency
        if card_count != total_cards_in_process:
            print(f"⚠️ Warning: Card count mismatch (data.json: {card_count}, process.json: {total_cards_in_process})")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading files: {e}")
        return False


def get_progress_info():
    """Get progress information from process.json."""
    
    process_file = Path("output/process.json")
    
    if not process_file.exists():
        print("📊 No progress file found - starting fresh")
        return 0
    
    try:
        with open(process_file, 'r', encoding='utf-8') as f:
            process = json.load(f)
        
        scraped_pages = process.get('scraped_pages', [])
        last_scraped = max(scraped_pages) if scraped_pages else 0
        
        print(f"📂 Found progress file")
        print(f"📊 Last scraped page: {last_scraped}")
        print(f"📄 Total pages completed: {len(scraped_pages)}")
        
        return last_scraped
        
    except Exception as e:
        print(f"⚠️ Error reading progress file: {e}")
        return 0


def main():
    """Main function - determine action based on command line argument."""
    
    if len(sys.argv) < 2:
        print("Usage: python run.py <action>")
        print("Actions:")
        print("  verify    - Verify output files and generate GitHub Actions outputs")
        print("  progress  - Get progress information")
        sys.exit(1)
    
    action = sys.argv[1].lower()
    
    if action == "verify":
        success = verify_output_files()
        sys.exit(0 if success else 1)
        
    elif action == "progress":
        last_page = get_progress_info()
        print(last_page)  # Output for shell capture
        sys.exit(0)
        
    else:
        print(f"❌ Unknown action: {action}")
        sys.exit(1)


if __name__ == "__main__":
    main()
