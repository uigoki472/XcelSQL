"""Validation utilities for xcelsql inputs."""
from __future__ import annotations
from typing import List, Dict, Any, Optional
import re
import pandas as pd
import os
from xcelsql.utils.constants import FORBIDDEN_SQL_TOKENS, FORBIDDEN_SHEET_NAME_PATTERN

# Compile regex patterns once
FORBIDDEN_SQL_REGEX = re.compile(r'\b(' + '|'.join(FORBIDDEN_SQL_TOKENS) + r')\b', re.IGNORECASE)
SHEET_NAME_RE = re.compile(FORBIDDEN_SHEET_NAME_PATTERN)

class ValidationError(Exception):
    """Exception raised for validation failures."""
    pass

def validate_input_file(filepath: str) -> None:
    """Validate that input file exists and is readable."""
    if not os.path.exists(filepath):
        raise ValidationError(f"Input file not found: {filepath}")
    
    if not os.path.isfile(filepath):
        raise ValidationError(f"Path is not a file: {filepath}")
    
    if not os.access(filepath, os.R_OK):
        raise ValidationError(f"File not readable: {filepath}")
    
    # Verify file extension
    if not filepath.lower().endswith(('.xlsx', '.xls', '.xlsm')):
        raise ValidationError(f"Unsupported file format: {filepath}")

def validate_output_path(filepath: str, create_dirs: bool = False) -> None:
    """Validate that output path is writable."""
    if not filepath:
        return
        
    directory = os.path.dirname(filepath)
    if directory and not os.path.exists(directory):
        if create_dirs:
            try:
                os.makedirs(directory, exist_ok=True)
            except Exception as e:
                raise ValidationError(f"Failed to create directory: {e}")
        else:
            raise ValidationError(f"Output directory does not exist: {directory}")
    
    if directory and not os.access(directory, os.W_OK):
        raise ValidationError(f"Output directory not writable: {directory}")

def validate_query(query: str, available_sheets: List[str], strict: bool = False) -> None:
    """Validate SQL query for security and correctness."""
    if not query:
        return
        
    stripped = query.lstrip()
    if not stripped.upper().startswith("SELECT"):
        raise ValidationError("Only SELECT queries are permitted")
        
    # Check for forbidden SQL tokens, handling string literals appropriately
    sanitized = re.sub(r"'[^']*'", "''", stripped)
    sanitized = re.sub(r'"[^"]*"', '""', sanitized)
    
    for match in FORBIDDEN_SQL_REGEX.finditer(sanitized):
        raise ValidationError(f"Query contains forbidden token: {match.group(1).upper()}")
    
    # Validate sheet references
    refs = list(re.finditer(r'\{([^}]+)\}', query))
    if strict and not refs:
        raise ValidationError("No sheet placeholders found in query under strict mode")
    
    for m in refs:
        ref = m.group(1)
        if ref not in available_sheets:
            raise ValidationError(f"Query references unknown sheet: '{ref}'")

def validate_sheet_names(sheet_names: List[str], strict: bool = False) -> None:
    """Validate sheet names against pattern if strict mode enabled."""
    if not strict:
        return
        
    for name in sheet_names:
        if not SHEET_NAME_RE.match(name):
            raise ValidationError(f"Sheet name '{name}' fails pattern {FORBIDDEN_SHEET_NAME_PATTERN}")

def validate_template(template_path: str, required_sheets: List[str] = None) -> None:
    """Validate that template file exists and has required sheets."""
    if not os.path.exists(template_path):
        raise ValidationError(f"Template file not found: {template_path}")
    
    if required_sheets:
        try:
            with pd.ExcelFile(template_path) as xls:
                available = xls.sheet_names
                for sheet in required_sheets:
                    if sheet not in available:
                        raise ValidationError(f"Required sheet '{sheet}' not found in template")
        except Exception as e:
            raise ValidationError(f"Failed to read template sheets: {e}")