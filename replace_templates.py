#!/usr/bin/env python3
"""
replace_templates.py

Automates replacement of {{CatDiffuse}} and variants with {{Diffusion by condition|200}}
in category pages, removing redundant templates.

Behavior:
  Single template with default limit:
    "{{CatDiffuse}}" → "{{Diffusion by condition|200}}"
  
  Preserves custom limit:
    "{{CatDiffuse|150}}" → "{{Diffusion by condition|150}}"
  
  Multiple templates - replaces first, removes rest:
    "{{CatDiffuse}} text {{Cat diffuse}}" → "{{Diffusion by condition|200}} text"
  
  Already has replacement - removes old only:
    "{{Diffusion by condition|200}} {{CatDiffuse}}" → "{{Diffusion by condition|200}}"

Usage:
  python replace_templates.py --dry-run --verbose --limit 5
  python replace_templates.py --category "Category:Example"
"""

import argparse
import logging
import re
import sys
import time
from typing import List, Tuple, Optional

import pywikibot
from pywikibot import pagegenerators
from pywikibot.exceptions import (
    EditConflictError,
    LockedPageError,
    NoPageError,
    OtherPageSaveError,
)

import config


def normalize_template_name(name: str) -> str:
    """
    Normalize template name for case-insensitive comparison.
    
    Args:
        name: Template name to normalize
    
    Returns:
        Lowercase, stripped template name
    """
    # Remove namespace prefix if present
    if ':' in name:
        name = name.split(':', 1)[1]
    return name.strip().lower().replace('_', ' ')


def extract_limit_from_template(text: str, template_name: str) -> Optional[int]:
    """
    Extract custom limit parameter from a template.
    
    Args:
        text: Template wikitext
        template_name: Name of the template to search for
    
    Returns:
        Integer limit if found, None otherwise
    """
    # Pattern to match {{TemplateName|limit}} or {{TemplateName|150}}
    normalized_name = normalize_template_name(template_name)
    
    # Try to find numbered parameter: {{Template|150}}
    pattern = r'\{\{\s*' + re.escape(template_name) + r'\s*\|\s*(\d+)\s*\}\}'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    
    # Try to find named parameter: {{Template|limit=150}}
    pattern = r'\{\{\s*' + re.escape(template_name) + r'\s*\|\s*limit\s*=\s*(\d+)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    
    return None


def has_target_template(text: str, target: str) -> bool:
    """
    Check if text already contains the target template.
    
    Args:
        text: Wikitext to search
        target: Target template name
    
    Returns:
        True if target template found
    """
    pattern = r'\{\{\s*' + re.escape(target) + r'\s*[\|\}]'
    return bool(re.search(pattern, text, re.IGNORECASE))


def replace_templates(
    text: str,
    source_templates: List[str],
    target_template: str,
    default_limit: int
) -> Tuple[str, bool, str]:
    """
    Replace source templates with target template, handling duplicates and limits.
    
    Behavior:
    - If target already exists, remove all source templates
    - Otherwise, replace first source template (preserving limit), remove rest
    - Extract custom limit from first source template
    
    Args:
        text: Category page wikitext
        source_templates: List of source template names (e.g., ['CatDiffuse', 'Cat diffuse'])
        target_template: Target template name (e.g., 'Diffusion by condition')
        default_limit: Default limit value if not specified
    
    Returns:
        Tuple of (new_text, changed, action_description)
    """
    original_text = text
    changed = False
    action = ""
    
    # Check if target template already exists
    target_exists = has_target_template(text, target_template)
    
    # Find all source templates
    source_found = []
    for source in source_templates:
        pattern = r'\{\{\s*' + re.escape(source) + r'\s*(\|[^\}]*)?\}\}'
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        if matches:
            source_found.extend([(source, m) for m in matches])
    
    if not source_found:
        return text, False, "No source templates found"
    
    # Sort by position in text
    source_found.sort(key=lambda x: x[1].start())
    
    if target_exists:
        # Target already exists - just remove all source templates
        # Remove from end to start to avoid position shifting issues
        for source, match in reversed(source_found):
            text = text[:match.start()] + text[match.end():]
        
        # Remove extra blank lines
        text = re.sub(r'\n\n+', '\n\n', text)
        # Clean up extra spaces
        text = re.sub(r'  +', ' ', text)
        changed = True
        action = "Removed redundant source templates (target already exists)"
    else:
        # Replace first source template, remove rest
        first_source, first_match = source_found[0]
        
        # Extract custom limit from first template
        custom_limit = extract_limit_from_template(first_match.group(0), first_source)
        limit = custom_limit if custom_limit else default_limit
        
        # Build replacement template
        replacement = f'{{{{{target_template}|{limit}}}}}'
        
        # Replace first occurrence
        text = text[:first_match.start()] + replacement + text[first_match.end():]
        offset = len(replacement) - len(first_match.group(0))
        
        # Remove remaining source templates
        for source, match in source_found[1:]:
            # Adjust position based on previous changes
            new_start = match.start() + offset if match.start() > first_match.start() else match.start()
            new_end = match.end() + offset if match.end() > first_match.start() else match.end()
            
            text = text[:new_start] + text[new_end:]
            offset -= (new_end - new_start)
        
        # Clean up extra blank lines
        text = re.sub(r'\n\n+', '\n\n', text)
        
        changed = True
        action = f"Replaced {first_source} with {target_template}|{limit}" + \
                (f" and removed {len(source_found)-1} duplicate(s)" if len(source_found) > 1 else "")
    
    return text, changed, action


def process_category(
    page: pywikibot.Page,
    source_templates: List[str],
    target_template: str,
    default_limit: int,
    dry_run: bool,
    verbose: bool
) -> bool:
    """
    Process a single category page for template replacement.
    
    Args:
        page: Category page to process
        source_templates: Source template names
        target_template: Target template name
        default_limit: Default limit value
        dry_run: If True, don't save changes
        verbose: If True, log verbose output
    
    Returns:
        True if processed successfully
    """
    try:
        text = page.text
        new_text, changed, action = replace_templates(
            text,
            source_templates,
            target_template,
            default_limit
        )
        
        if not changed:
            if verbose:
                logging.info(f"No changes needed for {page.title()}")
            return True
        
        if dry_run:
            logging.info(f"[DRY-RUN] Would update {page.title()}: {action}")
            if verbose:
                logging.debug(f"Old text:\n{text}\n")
                logging.debug(f"New text:\n{new_text}\n")
        else:
            # Determine appropriate edit summary
            if "Removed redundant" in action:
                summary = config.EDIT_SUMMARY_REMOVED_REDUNDANT
            else:
                # Extract limit from action
                limit_match = re.search(r'\|(\d+)', action)
                limit = limit_match.group(1) if limit_match else default_limit
                summary = config.EDIT_SUMMARY.format(limit=limit)
            
            page.text = new_text
            page.save(summary=summary, minor=False, botflag=True)
            logging.info(f"Updated {page.title()}: {action}")
        
        return True
        
    except NoPageError:
        logging.warning(f"Page not found: {page.title()}")
        return False
    except LockedPageError:
        logging.warning(f"Page is locked: {page.title()}")
        return False
    except EditConflictError:
        logging.warning(f"Edit conflict on: {page.title()}")
        return False
    except OtherPageSaveError as e:
        logging.error(f"Error saving {page.title()}: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error processing {page.title()}: {e}")
        return False


def main():
    """Main bot execution."""
    parser = argparse.ArgumentParser(
        description='Replace CatDiffuse templates with Diffusion by condition'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        default=config.DRY_RUN_DEFAULT,
        help='Preview changes without saving (default: True)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=0,
        help='Limit number of pages to process (0 = no limit)'
    )
    parser.add_argument(
        '--category',
        type=str,
        help='Process only pages in this category'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=config.DEFAULT_DELAY,
        help=f'Seconds to wait between edits (default: {config.DEFAULT_DELAY})'
    )
    parser.add_argument(
        '--templates',
        type=str,
        help='Comma-separated source template names (overrides config)'
    )
    parser.add_argument(
        '--default-limit',
        type=int,
        default=config.DEFAULT_LIMIT,
        help=f'Default limit value (default: {config.DEFAULT_LIMIT})'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(config.LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Use custom templates if provided
    source_templates = config.SOURCE_TEMPLATES
    if args.templates:
        source_templates = [t.strip() for t in args.templates.split(',')]
    
    mode = "DRY-RUN" if args.dry_run else "LIVE"
    logging.info(f"=== Template Replacement Bot [{mode}] ===")
    logging.info(f"Source templates: {', '.join(source_templates)}")
    logging.info(f"Target template: {config.TARGET_TEMPLATE}")
    logging.info(f"Default limit: {args.default_limit}")
    
    # Connect to Wikimedia Commons
    site = pywikibot.Site(config.WIKI_FAMILY, config.WIKI_LANG)
    site.login()
    logging.info(f"Logged in as {site.user()} on {site}")
    
    # Build page generator
    if args.category:
        # Process specific category
        cat = pywikibot.Category(site, args.category)
        gen = cat.members(namespaces=[14])  # Only category pages
        logging.info(f"Processing categories in: {args.category}")
    else:
        # Process all pages with source templates
        generators = []
        for template_name in source_templates:
            template = pywikibot.Page(site, f"Template:{template_name}")
            # Use template.embeddedin() instead of ReferringPageGenerator
            gen = template.embeddedin(namespaces=[14])  # Only category pages
            generators.append(gen)
        
        # Combine generators
        from itertools import chain
        gen = chain(*generators)
        logging.info(f"Processing all category pages with source templates")
    
    # Apply limit if specified
    if args.limit > 0:
        gen = pagegenerators.PreloadingGenerator(gen, groupsize=args.limit)
        logging.info(f"Processing limit: {args.limit} pages")
    
    # Process pages
    processed = 0
    updated = 0
    
    for page in gen:
        if args.limit > 0 and processed >= args.limit:
            break
        
        processed += 1
        success = process_category(
            page,
            source_templates,
            config.TARGET_TEMPLATE,
            args.default_limit,
            args.dry_run,
            args.verbose
        )
        
        if success:
            updated += 1
        
        # Rate limiting
        if not args.dry_run and processed < (args.limit or float('inf')):
            time.sleep(args.delay)
    
    # Summary
    logging.info(f"=== Summary ===")
    logging.info(f"Pages processed: {processed}")
    logging.info(f"Pages updated: {updated}")
    if args.dry_run:
        logging.info("DRY-RUN mode - no actual changes made")


if __name__ == '__main__':
    main()
