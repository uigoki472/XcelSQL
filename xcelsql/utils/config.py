"""Configuration management for xcelsql application."""
from __future__ import annotations
from typing import Dict, Any, Optional
import os
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = {
    "output_format": "excel",
    "header_row": 1,
    "allow_eval": False,
    "strict": False,
    "limit": None,
    "column_width": 30,
    "cache_enabled": True,
    "cache_dir": "~/.transformer_cache"
}

class Config:
    """Configuration manager for xcelsql settings."""
    
    def __init__(self):
        self.settings: Dict[str, Any] = DEFAULT_CONFIG.copy()
        self.config_file = os.path.expanduser("~/.transformer_config.json")
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from file if exists."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.settings.update(json.load(f))
        except Exception as e:
            logger.warning(f"Failed to load config: {e}")
    
    def save(self) -> None:
        """Save current configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        self.settings[key] = value
    
    def ensure_cache_dir(self) -> str:
        """Ensure cache directory exists and return its path."""
        cache_dir = os.path.expanduser(self.settings.get("cache_dir", DEFAULT_CONFIG["cache_dir"]))
        os.makedirs(cache_dir, exist_ok=True)
        return cache_dir

# Global config instance
config = Config()