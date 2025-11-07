"""
Caching system for TaskTitan.

This module provides a memory-efficient caching layer for frequently
accessed data to improve application performance.
"""

import time
from typing import Any, Optional, Dict, Callable
from collections import OrderedDict
from threading import Lock
from app.utils.logger import get_logger
from app.core.config import get_config

logger = get_logger(__name__)


class LRUCache:
    """Least Recently Used cache implementation."""
    
    def __init__(self, max_size: int = 100):
        """
        Initialize LRU cache.
        
        Args:
            max_size: Maximum number of items to cache
        """
        self.max_size = max_size
        self.cache: OrderedDict = OrderedDict()
        self.lock = Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get item from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        with self.lock:
            if key in self.cache:
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                return self.cache[key]
            return None
    
    def set(self, key: str, value: Any):
        """
        Set item in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        with self.lock:
            if key in self.cache:
                # Update existing
                self.cache.move_to_end(key)
            else:
                # Check if we need to evict
                if len(self.cache) >= self.max_size:
                    # Remove least recently used (first item)
                    self.cache.popitem(last=False)
            
            self.cache[key] = value
    
    def remove(self, key: str):
        """Remove item from cache."""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
    
    def clear(self):
        """Clear all cached items."""
        with self.lock:
            self.cache.clear()
    
    def size(self) -> int:
        """Get current cache size."""
        return len(self.cache)


class TimedCache:
    """Cache with time-based expiration."""
    
    def __init__(self, default_ttl: int = 300):
        """
        Initialize timed cache.
        
        Args:
            default_ttl: Default time-to-live in seconds
        """
        self.default_ttl = default_ttl
        self.cache: Dict[str, tuple[Any, float]] = {}
        self.lock = Lock()
    
    def get(self, key: str, ttl: Optional[int] = None) -> Optional[Any]:
        """
        Get item from cache.
        
        Args:
            key: Cache key
            ttl: Time-to-live override
            
        Returns:
            Cached value or None if expired
        """
        with self.lock:
            if key in self.cache:
                value, expiry = self.cache[key]
                if time.time() < expiry:
                    return value
                else:
                    # Expired, remove it
                    del self.cache[key]
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set item in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        with self.lock:
            expiry = time.time() + (ttl or self.default_ttl)
            self.cache[key] = (value, expiry)
    
    def remove(self, key: str):
        """Remove item from cache."""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
    
    def clear(self):
        """Clear all cached items."""
        with self.lock:
            self.cache.clear()
    
    def cleanup_expired(self):
        """Remove expired items."""
        with self.lock:
            current_time = time.time()
            expired_keys = [
                key for key, (_, expiry) in self.cache.items()
                if current_time >= expiry
            ]
            for key in expired_keys:
                del self.cache[key]
            
            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")


class CacheManager:
    """Centralized cache manager."""
    
    _instance: Optional['CacheManager'] = None
    
    def __init__(self):
        """Initialize cache manager."""
        if CacheManager._instance is not None:
            return
        
        cache_enabled = get_config('performance.cache_enabled', True)
        cache_size = get_config('performance.cache_size_mb', 100)
        
        # Convert MB to approximate item count (assuming avg 1KB per item)
        max_items = (cache_size * 1024 * 1024) // 1024
        
        self.enabled = cache_enabled
        self.lru_cache = LRUCache(max_items) if cache_enabled else None
        self.timed_cache = TimedCache() if cache_enabled else None
        
        CacheManager._instance = self
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get item from cache.
        
        Args:
            key: Cache key
            default: Default value if not found
            
        Returns:
            Cached value or default
        """
        if not self.enabled or not self.lru_cache:
            return default
        
        return self.lru_cache.get(key) or default
    
    def set(self, key: str, value: Any):
        """
        Set item in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        if not self.enabled or not self.lru_cache:
            return
        
        self.lru_cache.set(key, value)
    
    def invalidate(self, key: str):
        """Invalidate cache entry."""
        if self.lru_cache:
            self.lru_cache.remove(key)
        if self.timed_cache:
            self.timed_cache.remove(key)
    
    def invalidate_pattern(self, pattern: str):
        """
        Invalidate all cache entries matching pattern.
        
        Args:
            pattern: Pattern to match (simple substring match)
        """
        if not self.lru_cache:
            return
        
        keys_to_remove = [
            key for key in self.lru_cache.cache.keys()
            if pattern in key
        ]
        
        for key in keys_to_remove:
            self.invalidate(key)
    
    def clear(self):
        """Clear all caches."""
        if self.lru_cache:
            self.lru_cache.clear()
        if self.timed_cache:
            self.timed_cache.clear()
    
    @classmethod
    def get_instance(cls) -> 'CacheManager':
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


def cached(key_prefix: str = "", ttl: Optional[int] = None):
    """
    Decorator for caching function results.
    
    Args:
        key_prefix: Prefix for cache key
        ttl: Time-to-live in seconds (uses timed cache if provided)
    """
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            cache_manager = CacheManager.get_instance()
            
            if not cache_manager.enabled:
                return func(*args, **kwargs)
            
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            if ttl:
                result = cache_manager.timed_cache.get(cache_key, ttl)
            else:
                result = cache_manager.lru_cache.get(cache_key)
            
            if result is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return result
            
            # Cache miss, compute result
            logger.debug(f"Cache miss: {cache_key}")
            result = func(*args, **kwargs)
            
            # Store in cache
            if ttl:
                cache_manager.timed_cache.set(cache_key, result, ttl)
            else:
                cache_manager.lru_cache.set(cache_key, result)
            
            return result
        
        return wrapper
    return decorator

