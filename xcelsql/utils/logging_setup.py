"""Logging configuration for xcelsql application."""
from __future__ import annotations
import logging
import sys
from typing import Optional

DEFAULT_FORMAT = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'

def configure_logging(level: str = "INFO", 
                      log_file: Optional[str] = None, 
                      format_str: Optional[str] = None) -> None:
    """Configure logging with consistent format and options.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path to write logs to
        format_str: Optional custom format string
    """
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}")
    
    log_format = format_str or DEFAULT_FORMAT
    handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(logging.Formatter(log_format))
    handlers.append(console_handler)
    
    # File handler (if specified)
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter(log_format))
            handlers.append(file_handler)
        except Exception as e:
            print(f"Warning: Could not configure log file: {e}", file=sys.stderr)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add our handlers
    for handler in handlers:
        root_logger.addHandler(handler)
    
    # Set DuckDB logging level higher to reduce noise
    logging.getLogger("duckdb").setLevel(logging.WARNING)

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)