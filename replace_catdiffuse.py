#!/usr/bin/env python3
"""
replace_catdiffuse.py

Find Category: pages that transclude Template:CatDiffuse (or a list of templates),
count files in that category, and when the number of files <= THRESHOLD,
replace the template with Template:Diffusion by condition (preserving params).

Usage examples:
  python3 replace_catdiffuse.py --templates "CatDiffuse" --threshold 200 --dry-run --limit 10
  python3 replace_catdiffuse.py --templates "CatDiffuse,CatDiffuse2" --threshold 200
"""

import argparse
import logging
import time
import sys

import pywikibot
import mwparserfromhell
from pywikibot import pagegenerators
from pywikibot.exceptions import (
    EditConflictError, LockedPageError, OtherPageSaveError, SpamblacklistError
)

# Utility: count files in category, stop early if > threshold
def count_files_in_category(cat_page, threshold):
    """
    Count files in a category, short-circuiting if count exceeds threshold.
    
    Args:
        cat_page: pywikibot.Page in namespace 14 (Category)
        threshold: int, maximum count before short-circuit
    
    Returns:
        int: number of files found (capped at threshold + 1)
    """
    count = 0
    cat = pywikibot.Category(cat_page.site, cat_page.title())
    gen = cat.members(namespaces=[6], total=threshold + 1)  # namespace 6 = File
    for _ in gen:
        count += 1
        if count > threshold:
            break
    return count

def normalize_template_name(name):
    """Normalize template name for comparison (strip spaces, lowercase)."""
    return name.strip().lower()

def find_and_replace_templates(page_text, source_template_names, target_template_name, threshold_value, preserve_params=True):
    """
    Parse text with mwparserfromhell. Replace occurrences of any template in source_template_names
    with target_template_name. Returns (new_text, changed_flag, detected_threshold).
    
    Args:
        page_text: str, the wikitext to parse
        source_template_names: list of str, template names to replace
        target_template_name: str, replacement template name
        threshold_value: int, default value for threshold parameter
        preserve_params: bool, whether to preserve existing parameters
    
    Returns:
        tuple: (new_text, changed, detected_threshold) where detected_threshold is the value
               found in the original template (or None if not present)
    """
    parsed = mwparserfromhell.parse(page_text)
    changed = False
    detected_threshold = None
    src_normal = set(normalize_template_name(n) for n in source_template_names)

    # iterate over templates (we create a list copy because we'll modify parsed)
    for tpl in list(parsed.filter_templates()):
        tpl_name = normalize_template_name(str(tpl.name))
        # sometimes names have namespace like "Template:CatDiffuse" — handle that
        if tpl_name.startswith('template:'):
            tpl_name = tpl_name.split(':', 1)[1].strip()

        if tpl_name in src_normal:
            # Check if template already has a threshold parameter
            existing_threshold = None
            for p in tpl.params:
                param_name = str(p.name).strip().lower()
                if param_name == 'threshold':
                    try:
                        existing_threshold = int(str(p.value).strip())
                        detected_threshold = existing_threshold
                    except (ValueError, TypeError):
                        pass
            
            # Use existing threshold if found, otherwise use default
            final_threshold = existing_threshold if existing_threshold is not None else threshold_value
            
            # Build the new template node
            new_tpl = mwparserfromhell.nodes.Template(target_template_name)
            if preserve_params:
                # copy all params from old template to new template
                for p in tpl.params:
                    new_tpl.add(p.name, p.value)
            # ensure threshold parameter exists (only add if not present)
            if 'threshold' not in (str(p.name).strip().lower() for p in new_tpl.params):
                new_tpl.add('threshold', str(final_threshold))

            # replace the old template node with the new one
            parsed.replace(tpl, new_tpl)
            changed = True

    return str(parsed), changed, detected_threshold

def main():
    parser = argparse.ArgumentParser(description='Replace CatDiffuse templates with Diffusion by condition based on file counts.')
    parser.add_argument('--templates', default='CatDiffuse', help='Comma-separated source template names (without "Template:"), e.g. "CatDiffuse,CatDiffuse2"')
    parser.add_argument('--target', default='Diffusion by condition', help='Target template name (exact page title without "Template:")')
    parser.add_argument('--threshold', type=int, default=200, help='File count threshold (default 200)')
    parser.add_argument('--dry-run', action='store_true', help='Do not save changes; just show what would be changed')
    parser.add_argument('--limit', type=int, default=0, help='Limit number of categories to process (0 = no limit)')
    parser.add_argument('--delay', type=float, default=5.0, help='Seconds to wait between edits')
    parser.add_argument('--site', default='commons', help='Site family code used by pywikibot (default: commons)')
    parser.add_argument('--summary', default=None, help='Edit summary (default auto-generated)')
    parser.add_argument('--log', default='replace_catdiffuse.log', help='Log file path')
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s',
        handlers=[
            logging.FileHandler(args.log),
            logging.StreamHandler(sys.stdout)
        ]
    )

    site = pywikibot.Site(args.site, args.site)  # family, lang both set to args.site often works for commons
    site.login()  # ensure logged in (will prompt if necessary)
    logging.info('Logged in as %s on %s', site.user(), site)

    source_templates = [t.strip() for t in args.templates.split(',') if t.strip()]
    target_template = args.target

    processed = 0
    total_candidates = 0

    # For each source template, get categories that embed it (namespace=14)
    for src in source_templates:
        tpl_page = pywikibot.Page(site, 'Template:' + src)
        logging.info('Searching categories embedding Template:%s ...', src)
        # embeddedin returns pages that embed the template; filter to namespace 14 (Category)
        try:
            gen = tpl_page.embeddedin(namespaces=[14])
        except Exception as e:
            logging.exception('Failed to get embeddedin for Template:%s: %s', src, e)
            continue

        for cat_page in gen:
            total_candidates += 1
            if args.limit and processed >= args.limit:
                logging.info('Reached processing limit (%d)', args.limit)
                break

            title = cat_page.title()
            try:
                text = cat_page.get()
            except Exception as e:
                logging.warning('Could not get page %s: %s', title, e)
                continue

            # quick check for presence of source template text to skip parsing if not present
            if all(s.lower() not in text.lower() for s in source_templates):
                continue

            # Count files (namespace 6). Short-circuit if > threshold.
            file_count = count_files_in_category(cat_page, args.threshold)
            logging.info('Category %s has %d files (threshold=%d)', title, file_count, args.threshold)

            if file_count <= args.threshold:
                new_text, changed, detected_threshold = find_and_replace_templates(text, [src], target_template, args.threshold)
                if changed:
                    # Use detected threshold from template if found, otherwise CLI default
                    used_threshold = detected_threshold if detected_threshold is not None else args.threshold
                    logging.info('Would replace in %s (using threshold=%d)', title, used_threshold)
                    if args.dry_run:
                        logging.info('[dry-run] %s would be saved (files=%d, threshold=%d)', title, file_count, used_threshold)
                    else:
                        # Save changes
                        page = pywikibot.Page(site, title)
                        used_threshold = detected_threshold if detected_threshold is not None else args.threshold
                        edit_summary = args.summary or f'Bot: Replace {src} with {target_template} (threshold={used_threshold})'
                        try:
                            page.text = new_text
                            page.save(summary=edit_summary)
                            logging.info('Saved %s', title)
                        except (EditConflictError, LockedPageError, SpamblacklistError, OtherPageSaveError) as e:
                            logging.warning('Could not save %s: %s', title, e)
                        except Exception as e:
                            logging.exception('Unexpected error while saving %s: %s', title, e)

                        time.sleep(args.delay)

                    processed += 1
                else:
                    logging.info('No matching template instance found in %s', title)
            else:
                logging.debug('Category %s skipped (files=%d > threshold=%d)', title, file_count, args.threshold)

        if args.limit and processed >= args.limit:
            break

    logging.info('Done. Processed %d categories (candidates seen: %d)', processed, total_candidates)

if __name__ == '__main__':
    main()
