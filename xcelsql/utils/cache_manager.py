"""Cache management for worksheet data to improve performance."""
from __future__ import annotations
from typing import Dict, Optional, Any, Tuple
import os
import json
import hashlib
import pickle
import logging
import time
import pandas as pd
from .config import config

logger = logging.getLogger(__name__)

class CacheManager:
    """Manages caching of worksheet data and metadata."""
    
    def __init__(self):
        self.enabled = config.get("cache_enabled", True)
        self.cache_dir = config.ensure_cache_dir()
        self.meta_cache: Dict[str, Dict[str, Any]] = {}
        
    def _get_file_hash(self, path: str) -> str:
        """Generate a hash based on file path and modification time."""
        try:
            stat = os.stat(path)
            key = f"{path}:{stat.st_mtime_ns}:{stat.st_size}"
            return hashlib.md5(key.encode()).hexdigest()
        except Exception as e:
            logger.warning(f"Failed to hash file {path}: {e}")
            return hashlib.md5(path.encode()).hexdigest()
    
    def _get_cache_path(self, file_hash: str, sheet_name: str, header_row: int) -> str:
        """Get the cache file path for a given sheet."""
        safe_sheet = sheet_name.replace('/', '_').replace('\\', '_')
        return os.path.join(self.cache_dir, f"{file_hash}_{safe_sheet}_{header_row}.pkl")
    
    def _get_meta_path(self, file_hash: str) -> str:
        """Get the path for metadata cache file."""
        return os.path.join(self.cache_dir, f"{file_hash}_meta.json")
    
    def get_cached_sheet(self, excel_path: str, sheet_name: str, header_row: int) -> Optional[pd.DataFrame]:
        """Retrieve sheet data from cache if available and still valid."""
        if not self.enabled:
            return None
            
        try:
            file_hash = self._get_file_hash(excel_path)
            cache_path = self._get_cache_path(file_hash, sheet_name, header_row)
            
            if not os.path.exists(cache_path):
                return None
                
            # Check if cache is still valid
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.debug(f"Cache retrieval failed: {e}")
            return None
    
    def cache_sheet(self, excel_path: str, sheet_name: str, header_row: int, df: pd.DataFrame) -> None:
        """Cache sheet data for future use."""
        if not self.enabled:
            return
            
        try:
            file_hash = self._get_file_hash(excel_path)
            cache_path = self._get_cache_path(file_hash, sheet_name, header_row)
            
            with open(cache_path, 'wb') as f:
                pickle.dump(df, f)
                
            logger.debug(f"Cached sheet {sheet_name} to {cache_path}")
        except Exception as e:
            logger.warning(f"Failed to cache sheet {sheet_name}: {e}")
    
    def get_meta(self, excel_path: str) -> Dict[str, Any]:
        """Get metadata for Excel file from cache."""
        if not self.enabled:
            return {}
            
        try:
            file_hash = self._get_file_hash(excel_path)
            
            # Return from memory if already loaded
            if file_hash in self.meta_cache:
                return self.meta_cache[file_hash]
                
            meta_path = self._get_meta_path(file_hash)
            if os.path.exists(meta_path):
                with open(meta_path, 'r') as f:
                    self.meta_cache[file_hash] = json.load(f)
                    return self.meta_cache[file_hash]
        except Exception as e:
            logger.debug(f"Meta cache retrieval failed: {e}")
        
        return {}
    
    def save_meta(self, excel_path: str, meta_data: Dict[str, Any]) -> None:
        """Save metadata for Excel file to cache."""
        if not self.enabled:
            return
            
        try:
            file_hash = self._get_file_hash(excel_path)
            meta_path = self._get_meta_path(file_hash)
            
            # Update memory cache
            self.meta_cache[file_hash] = meta_data
            
            # Write to disk
            with open(meta_path, 'w') as f:
                json.dump(meta_data, f, indent=2)
                
            logger.debug(f"Saved metadata to {meta_path}")
        except Exception as e:
            logger.warning(f"Failed to save metadata: {e}")
    
    def clear_cache(self, excel_path: Optional[str] = None) -> int:
        """Clear cache for a specific file or all files.
        
        Returns:
            Number of cache files deleted
        """
        count = 0
        try:
            if excel_path:
                # Clear specific file cache
                file_hash = self._get_file_hash(excel_path)
                pattern = f"{file_hash}_"
                for filename in os.listdir(self.cache_dir):
                    if filename.startswith(pattern):
                        os.remove(os.path.join(self.cache_dir, filename))
                        count += 1
                # Clear from memory cache
                if file_hash in self.meta_cache:
                    del self.meta_cache[file_hash]
            else:
                # Clear all cache
                for filename in os.listdir(self.cache_dir):
                    if filename.endswith(('.pkl', '.json')):
                        os.remove(os.path.join(self.cache_dir, filename))
                        count += 1
                # Clear memory cache
                self.meta_cache.clear()
        except Exception as e:
            logger.warning(f"Error clearing cache: {e}")
        
        return count

# Global cache manager instance
cache_manager = CacheManager()