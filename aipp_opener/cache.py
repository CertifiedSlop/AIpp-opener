"""Caching utilities for AIpp Opener."""

import json
import hashlib
import time
from pathlib import Path
from typing import Optional, Any, Generic, TypeVar
from dataclasses import dataclass

from aipp_opener.logger_config import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


@dataclass
class CacheEntry(Generic[T]):
    """A cache entry with expiration."""
    
    value: T
    expires_at: float
    created_at: float
    
    def is_expired(self) -> bool:
        """Check if the entry has expired."""
        return time.time() > self.expires_at


class Cache(Generic[T]):
    """Generic cache with TTL support."""
    
    def __init__(
        self,
        name: str,
        ttl: int = 300,
        cache_dir: Optional[Path] = None
    ):
        """
        Initialize the cache.
        
        Args:
            name: Cache name (used for cache file).
            ttl: Time-to-live in seconds (default: 5 minutes).
            cache_dir: Directory for cache files.
        """
        self.name = name
        self.ttl = ttl
        
        if cache_dir is None:
            cache_dir = Path.home() / ".cache" / "aipp_opener"
        
        self.cache_dir = cache_dir
        self.cache_file = self.cache_dir / f"{name}.json"
        self._cache: dict[str, dict] = {}
        self._load()
        logger.debug("Cache initialized: %s (ttl=%ds, file=%s)", name, ttl, self.cache_file)
    
    def _load(self) -> None:
        """Load cache from file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r") as f:
                    self._cache = json.load(f)
                logger.debug("Loaded %d cache entries from %s", len(self._cache), self.cache_file)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning("Could not load cache file: %s", e)
                self._cache = {}
        else:
            self._cache = {}
    
    def _save(self) -> None:
        """Save cache to file."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.cache_file, "w") as f:
                json.dump(self._cache, f, indent=2)
            logger.debug("Saved %d cache entries to %s", len(self._cache), self.cache_file)
        except (IOError, OSError) as e:
            logger.warning("Could not save cache file: %s", e)
    
    def _generate_key(self, *args: Any, **kwargs: Any) -> str:
        """Generate a cache key from arguments."""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[T]:
        """
        Get a value from cache.
        
        Args:
            key: Cache key.
            
        Returns:
            Cached value or None if not found/expired.
        """
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        if time.time() > entry["expires_at"]:
            logger.debug("Cache entry expired: %s", key)
            del self._cache[key]
            return None
        
        logger.debug("Cache hit: %s", key)
        return entry["value"]
    
    def set(self, key: str, value: T) -> None:
        """
        Set a value in cache.
        
        Args:
            key: Cache key.
            value: Value to cache.
        """
        now = time.time()
        self._cache[key] = {
            "value": value,
            "expires_at": now + self.ttl,
            "created_at": now,
        }
        logger.debug("Cache set: %s (ttl=%ds)", key, self.ttl)
        self._save()
    
    def delete(self, key: str) -> bool:
        """
        Delete a key from cache.
        
        Args:
            key: Cache key.
            
        Returns:
            True if deleted, False if key not found.
        """
        if key in self._cache:
            del self._cache[key]
            self._save()
            logger.debug("Cache delete: %s", key)
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache = {}
        if self.cache_file.exists():
            self.cache_file.unlink()
        logger.info("Cache cleared: %s", self.name)
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries.
        
        Returns:
            Number of entries removed.
        """
        now = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if now > entry["expires_at"]
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            self._save()
            logger.debug("Cleaned up %d expired cache entries", len(expired_keys))
        
        return len(expired_keys)
    
    def __len__(self) -> int:
        """Return number of cache entries."""
        return len(self._cache)
    
    def stats(self) -> dict:
        """Get cache statistics."""
        now = time.time()
        expired = sum(
            1 for entry in self._cache.values()
            if now > entry["expires_at"]
        )
        
        return {
            "name": self.name,
            "total_entries": len(self._cache),
            "expired_entries": expired,
            "valid_entries": len(self._cache) - expired,
            "ttl": self.ttl,
        }


class AppDetectionCache(Cache[list[dict]]):
    """Specialized cache for app detection results."""
    
    def __init__(self, ttl: int = 600):
        """
        Initialize app detection cache.
        
        Args:
            ttl: Cache TTL in seconds (default: 10 minutes).
        """
        super().__init__("app_detection", ttl=ttl)
    
    def get_apps(self, detector_name: str) -> Optional[list[dict]]:
        """
        Get cached apps for a detector.
        
        Args:
            detector_name: Name of the detector.
            
        Returns:
            Cached app list or None.
        """
        return self.get(detector_name)
    
    def set_apps(self, detector_name: str, apps: list[dict]) -> None:
        """
        Cache apps for a detector.
        
        Args:
            detector_name: Name of the detector.
            apps: List of app dicts to cache.
        """
        self.set(detector_name, apps)
