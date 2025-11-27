#!/usr/bin/env python3
"""
category_diffusion_bot.py

Declutter bot that removes categories with <N files from "Category:Categories requiring temporary diffusion".
This allows editors to focus on large categories that need manual attention.

Usage:
  python3 category_diffusion_bot.py                    # Dry-run with default 200 threshold
  python3 category_diffusion_bot.py -live              # Execute removals
  python3 category_diffusion_bot.py -live -min:150     # Execute with 150-file threshold
  python3 category_diffusion_bot.py -limit:50          # Process only 50 categories
"""

import argparse
import logging
import sys
import time
from typing import List, Tuple

import pywikibot
from pywikibot.exceptions import (
    EditConflictError,
    LockedPageError,
    NoPageError,
    OtherPageSaveError,
)


# Configuration
DIFFUSION_CATEGORY = "Category:Categories requiring temporary diffusion"
DEFAULT_THRESHOLD = 200
EDIT_SUMMARY = "Bot: Removing category with <{threshold} files from diffusion list (decluttering)"


def count_files_in_category(category: pywikibot.Category, threshold: int) -> int:
    """
    Count files in a category, short-circuiting if count exceeds threshold.
    
    Args:
        category: pywikibot.Category object
        threshold: Maximum count before short-circuit
    
    Returns:
        Number of files found (capped at threshold + 1)
    """
    count = 0
    try:
        # namespace 6 = File namespace
        for _ in category.members(namespaces=[6], total=threshold + 1):
            count += 1
            if count > threshold:
                break
    except Exception as e:
        logging.warning(f"Error counting files in {category.title()}: {e}")
    return count


def get_subcategories(parent_category: pywikibot.Category) -> List[pywikibot.Category]:
    """
    Fetch all subcategories from the parent diffusion category.
    
    Args:
        parent_category: The parent category to fetch subcategories from
    
    Returns:
        List of Category objects
    """
    subcategories = []
    try:
        # namespace 14 = Category namespace
        for subcat in parent_category.members(namespaces=[14]):
            subcategories.append(pywikibot.Category(subcat))
    except Exception as e:
        logging.error(f"Error fetching subcategories: {e}")
    return subcategories


def remove_category_from_parent(
    category: pywikibot.Category,
    parent_category: pywikibot.Category,
    dry_run: bool,
    threshold: int
) -> bool:
    """
    Remove a category from its parent by removing the parent category tag.
    
    Args:
        category: Category to remove from parent
        parent_category: Parent category (diffusion list)
        dry_run: If True, don't save changes
        threshold: Threshold value for edit summary
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get the category page
        page = pywikibot.Page(category.site, category.title())
        text = page.get()
        
        # Look for the parent category tag (with or without pipe syntax)
        import re
        parent_title = parent_category.title()
        parent_tag = f"[[{parent_title}]]"
        parent_tag_with_pipe = f"[[{parent_title}|"
        
        # Check if parent category is present in any form
        if parent_tag not in text and parent_tag_with_pipe not in text:
            logging.debug(f"{category.title()} doesn't contain parent tag")
            return False
        
        # Remove the parent category tag (handles both [[Cat]] and [[Cat|Sort]] forms)
        new_text = text
        
        # First try simple replacement
        if parent_tag in text:
            new_text = new_text.replace(parent_tag, "")
        
        # Then handle pipe syntax with regex
        pattern = re.escape(parent_title).replace(':', r'\:')
        new_text = re.sub(
            rf'\[\[{pattern}\|[^\]]*\]\]',
            '',
            new_text
        )
        
        if new_text == text:
            logging.debug(f"No changes needed for {category.title()}")
            return False
        
        if dry_run:
            logging.info(f"[DRY-RUN] Would remove {category.title()} from diffusion list")
            return True
        
        # Save the changes
        page.text = new_text
        summary = EDIT_SUMMARY.format(threshold=threshold)
        page.save(summary=summary, minor=False)
        logging.info(f"✓ Removed {category.title()} from diffusion list")
        return True
        
    except NoPageError:
        logging.warning(f"Page not found: {category.title()}")
        return False
    except LockedPageError:
        logging.warning(f"Page is locked: {category.title()}")
        return False
    except EditConflictError:
        logging.warning(f"Edit conflict on: {category.title()}")
        return False
    except OtherPageSaveError as e:
        logging.error(f"Could not save {category.title()}: {e}")
        return False
    except Exception as e:
        logging.exception(f"Unexpected error processing {category.title()}: {e}")
        return False


def main():
    """Main bot execution."""
    parser = argparse.ArgumentParser(
        description='Declutter bot: Remove small categories from diffusion list'
    )
    parser.add_argument(
        '-live',
        action='store_true',
        help='Execute removals (default is dry-run)'
    )
    parser.add_argument(
        '-min',
        type=int,
        default=DEFAULT_THRESHOLD,
        help=f'Minimum file threshold (default: {DEFAULT_THRESHOLD})'
    )
    parser.add_argument(
        '-limit',
        type=int,
        default=0,
        help='Limit number of categories to process (0 = no limit)'
    )
    parser.add_argument(
        '-delay',
        type=float,
        default=5.0,
        help='Seconds to wait between edits (default: 5.0)'
    )
    parser.add_argument(
        '--log',
        default='category_diffusion_bot.log',
        help='Log file path'
    )
    
    args = parser.parse_args()
    
    # Handle -min:N format (pywikibot style)
    for arg in sys.argv[1:]:
        if arg.startswith('-min:'):
            args.min = int(arg.split(':')[1])
    
    dry_run = not args.live
    threshold = args.min
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(args.log),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    mode = "DRY-RUN" if dry_run else "LIVE"
    logging.info(f"=== Category Diffusion Decluttering Bot [{mode}] ===")
    logging.info(f"Threshold: {threshold} files")
    logging.info(f"Target: {DIFFUSION_CATEGORY}")
    
    # Connect to Wikimedia Commons
    site = pywikibot.Site('commons', 'commons')
    site.login()
    logging.info(f"Logged in as: {site.user()}")
    
    # Get the parent diffusion category
    parent_category = pywikibot.Category(site, DIFFUSION_CATEGORY)
    
    # Fetch all subcategories
    logging.info("Fetching subcategories from diffusion list...")
    subcategories = get_subcategories(parent_category)
    logging.info(f"Found {len(subcategories)} subcategories")
    
    if not subcategories:
        logging.warning("No subcategories found. Exiting.")
        return
    
    # Process each subcategory
    processed = 0
    removed = 0
    skipped = 0
    
    for i, subcat in enumerate(subcategories, 1):
        if args.limit and processed >= args.limit:
            logging.info(f"Reached processing limit ({args.limit})")
            break
        
        logging.info(f"[{i}/{len(subcategories)}] Processing: {subcat.title()}")
        
        # Count files in the category
        file_count = count_files_in_category(subcat, threshold)
        
        if file_count <= threshold:
            logging.info(f"  → {file_count} files (≤{threshold}) - removing from list")
            
            if remove_category_from_parent(subcat, parent_category, dry_run, threshold):
                removed += 1
                if not dry_run:
                    time.sleep(args.delay)  # Rate limiting
            else:
                skipped += 1
        else:
            logging.info(f"  → {file_count} files (>{threshold}) - keeping in list")
            skipped += 1
        
        processed += 1
    
    # Summary
    logging.info("=" * 60)
    logging.info(f"Processing complete!")
    logging.info(f"  Processed: {processed}")
    logging.info(f"  Removed: {removed}")
    logging.info(f"  Skipped: {skipped}")
    
    if dry_run:
        logging.info("")
        logging.info("This was a DRY-RUN. No changes were made.")
        logging.info("Run with -live flag to execute removals.")


if __name__ == '__main__':
    main()
