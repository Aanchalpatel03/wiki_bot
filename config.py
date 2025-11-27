#!/usr/bin/env python3
"""
config.py

Configuration for the CatDiffuse template replacement bot.
Contains template mappings, default limits, and edit summaries.
"""

# Template mappings
SOURCE_TEMPLATES = [
    'CatDiffuse',
    'Cat diffuse',
    'Category diffuse',
    'Catdiffuse',
]

TARGET_TEMPLATE = 'Diffusion by condition'

# Default limit for file count threshold
DEFAULT_LIMIT = 200

# Edit summaries
EDIT_SUMMARY = 'Bot: Replacing {{CatDiffuse}} with {{Diffusion by condition|{limit}}}'
EDIT_SUMMARY_REMOVED_REDUNDANT = 'Bot: Removing redundant {{CatDiffuse}} ({{Diffusion by condition}} already present)'

# Bot behavior settings
DEFAULT_DELAY = 5.0  # Seconds between edits
DRY_RUN_DEFAULT = True  # Default to dry-run for safety

# Logging settings
LOG_FILE = 'replace_templates.log'
LOG_LEVEL = 'INFO'

# Wikimedia Commons settings
WIKI_FAMILY = 'commons'
WIKI_LANG = 'commons'
