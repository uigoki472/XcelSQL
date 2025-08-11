"""String manipulation utilities for xcelsql."""
from __future__ import annotations
from typing import Dict, List, Set, Tuple
import re
import unicodedata

# Common string normalization
def normalize_string(s: str) -> str:
    """Normalize a string by removing special characters, spaces, and casing."""
    if not s:
        return ""
    # Unicode normalization (e.g., accented chars)
    s = unicodedata.normalize('NFKC', s)
    # Replace non-alphanumeric with underscore
    s = re.sub(r'[^\w]', '_', s)
    # Convert to lowercase
    return s.lower()

# Collection of quote characters for handling various quote styles
QUOTE_CHARS: Set[str] = {'"','"','"',''',''','«','»'}

def strip_quotes(s: str) -> str:
    """Strip various quote characters from string."""
    if not s:
        return s
    s2 = s.strip()
    # Strip multiple leading/trailing quote chars
    while s2 and s2[0] in QUOTE_CHARS:
        s2 = s2[1:]
    while s2 and s2[-1] in QUOTE_CHARS:
        s2 = s2[:-1]
    return s2.strip()

def sanitize_identifier(name: str) -> str:
    """Convert a string to a valid identifier."""
    if not name:
        return "unnamed"
    
    # Replace non-identifier chars with underscore
    clean = re.sub(r'[^\w]', '_', name)
    
    # Ensure it starts with a letter or underscore
    if not clean[0].isalpha() and clean[0] != '_':
        clean = 'x_' + clean
        
    return clean

def format_bytes(num: int) -> str:
    """Format byte size to human-readable format."""
    for unit in ['B','KB','MB','GB','TB']:
        if num < 1024:
            return f"{num:.1f}{unit}"
        num /= 1024
    return f"{num:.1f}PB"

def truncate_string(s: str, max_length: int = 50, suffix: str = '...') -> str:
    """Truncate a string to specified maximum length."""
    if not s or len(s) <= max_length:
        return s
    truncated_length = max_length - len(suffix)
    if truncated_length <= 0:
        return suffix
    return s[:truncated_length] + suffix