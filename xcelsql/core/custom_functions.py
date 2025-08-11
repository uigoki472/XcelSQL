"""Custom functions for expression evaluation."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
import re
import datetime
import pandas as pd
from xcelsql.core.expr_eval import register_custom_function

# String manipulation functions
def clean_string(s: Any) -> str:
    """Remove leading/trailing whitespace and normalize internal spacing."""
    if pd.isna(s):
        return ""
    return re.sub(r'\s+', ' ', str(s).strip())

register_custom_function('clean', clean_string)

def extract_number(s: Any) -> Optional[float]:
    """Extract the first number from a string."""
    if pd.isna(s):
        return None
    match = re.search(r'[-+]?\d*\.?\d+', str(s))
    if match:
        return float(match.group(0))
    return None

register_custom_function('extract_number', extract_number)

# Date functions
def format_date(dt: Any, fmt: str = '%Y-%m-%d') -> str:
    """Format a date object or string as specified format."""
    if pd.isna(dt):
        return ""
    try:
        if isinstance(dt, str):
            dt = pd.to_datetime(dt)
        return dt.strftime(fmt)
    except Exception:
        return str(dt)

register_custom_function('format_date', format_date)

def date_diff_days(start: Any, end: Any) -> Optional[int]:
    """Calculate days between two dates."""
    if pd.isna(start) or pd.isna(end):
        return None
    try:
        start_dt = pd.to_datetime(start)
        end_dt = pd.to_datetime(end)
        return (end_dt - start_dt).days
    except Exception:
        return None

register_custom_function('date_diff_days', date_diff_days)

# Conditional logic
def coalesce(*args: Any) -> Any:
    """Return first non-null value (similar to SQL COALESCE)."""
    for arg in args:
        if not pd.isna(arg):
            return arg
    return None

register_custom_function('coalesce', coalesce)

def case_when(condition: Any, true_val: Any, false_val: Any) -> Any:
    """Simple IF-THEN-ELSE function."""
    return true_val if condition else false_val

register_custom_function('case_when', case_when)

# Add more custom functions below as needed
def today() -> datetime.date:
    """Return current date."""
    return datetime.date.today()

register_custom_function('today', today)

# Initialize custom functions
def register_all_functions() -> None:
    """Ensure all custom functions are registered."""
    # This function can be called at startup if needed
    # All functions are already registered during import
    pass