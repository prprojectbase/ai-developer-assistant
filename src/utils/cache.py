"""
Caching utilities for AI Developer Assistant
"""

import asyncio
import json
import time
import hashlib
import pickle
from typing import Any, Dict, Optional, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import functools
import weakref

from ..config.settings import get_settings


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    size: int = 0
    
    def is_expired(self) -> bool:
        """Check if entry has expired"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def touch(self) -> None:
        """Update access information"""
        self.access_count += 1
        self.last_accessed = datetime.now()


class CacheManager:
    """High-performance caching manager"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.settings = get_settings()
        self.max_size = max_size
        self.default_ttl = default_ttl  # 5 minutes default
        
        # Cache storage
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order = []  # For LRU eviction
        
        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "size": 0,
            "total_entries": 0
        }
        
        # Cleanup task
        self.cleanup_task: Optional[asyncio.Task] = None
        self.is_running = False
        
        # Event loop
        self.event_loop = None
    
    async def initialize(self) -> None:
        """Initialize the cache manager"""
        self.event_loop = asyncio.get_event_loop()
        self.is_running = True
        
        # Start cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        # Load cached data from disk if available
        await self._load_from_disk()
    
    async def stop(self) -> None:
        """Stop the cache manager"""
        self.is_running = False
        
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Save cache to disk
        await self._save_to_disk()
    
    def _generate_key(self, key_parts: tuple) -> str:
        """Generate a cache key from parts"""
        key_str = ":".join(str(part) for part in key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _evict_lru(self) -> None:
        """Evict least recently used entries"""
        if len(self.cache) <= self.max_size:
            return
        
        # Sort by last access time
        sorted_entries = sorted(
            self.cache.values(),
            key=lambda x: x.last_accessed
        )
        
        # Evict oldest entries
        entries_to_remove = len(self.cache) - self.max_size
        for entry in sorted_entries[:entries_to_remove]:
            self._remove_entry(entry.key)
    
    def _remove_entry(self, key: str) -> None:
        """Remove an entry from cache"""
        if key in self.cache:
            entry = self.cache[key]
            del self.cache[key]
            self.stats["size"] -= entry.size
            self.stats["evictions"] += 1
    
    def _update_access_order(self, key: str) -> None:
        """Update access order for LRU"""
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get a value from cache"""
        if key in self.cache:
            entry = self.cache[key]
            
            if entry.is_expired():
                self._remove_entry(key)
                self.stats["misses"] += 1
                return default
            
            entry.touch()
            self._update_access_order(key)
            self.stats["hits"] += 1
            return entry.value
        
        self.stats["misses"] += 1
        return default
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in cache"""
        # Calculate size (approximate)
        try:
            size = len(pickle.dumps(value))
        except (pickle.PicklingError, TypeError):
            size = len(str(value).encode())
        
        # Check if we need to evict
        if len(self.cache) >= self.max_size:
            self._evict_lru()
        
        # Create entry
        expires_at = None
        if ttl is not None:
            expires_at = datetime.now() + timedelta(seconds=ttl)
        elif self.default_ttl > 0:
            expires_at = datetime.now() + timedelta(seconds=self.default_ttl)
        
        entry = CacheEntry(
            key=key,
            value=value,
            expires_at=expires_at,
            size=size
        )
        
        # Remove existing entry if any
        if key in self.cache:
            self._remove_entry(key)
        
        # Add new entry
        self.cache[key] = entry
        self.stats["size"] += size
        self.stats["total_entries"] += 1
        self._update_access_order(key)
    
    async def delete(self, key: str) -> bool:
        """Delete a value from cache"""
        if key in self.cache:
            self._remove_entry(key)
            if key in self.access_order:
                self.access_order.remove(key)
            return True
        return False
    
    async def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
        self.access_order.clear()
        self.stats["size"] = 0
        self.stats["evictions"] += len(self.cache)
    
    async def get_or_set(self, key: str, value_func: Callable, ttl: Optional[int] = None) -> Any:
        """Get value or set it using provided function"""
        value = await self.get(key)
        if value is None:
            value = await value_func()
            await self.set(key, value, ttl)
        return value
    
    def has(self, key: str) -> bool:
        """Check if key exists in cache"""
        return key in self.cache and not self.cache[key].is_expired()
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0
        
        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate": hit_rate,
            "evictions": self.stats["evictions"],
            "size_bytes": self.stats["size"],
            "size_mb": self.stats["size"] / (1024 * 1024),
            "total_entries": len(self.cache),
            "max_entries": self.max_size,
            "default_ttl": self.default_ttl
        }
    
    async def _cleanup_loop(self) -> None:
        """Background cleanup loop"""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Cleanup every minute
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error but continue
                pass
    
    async def _cleanup_expired(self) -> int:
        """Clean up expired entries"""
        expired_keys = []
        
        for key, entry in self.cache.items():
            if entry.is_expired():
                expired_keys.append(key)
        
        for key in expired_keys:
            self._remove_entry(key)
            if key in self.access_order:
                self.access_order.remove(key)
        
        return len(expired_keys)
    
    async def _save_to_disk(self) -> None:
        """Save cache to disk (optional feature)"""
        # This is a simplified implementation
        # In production, you'd want more sophisticated persistence
        try:
            cache_data = {}
            for key, entry in self.cache.items():
                if not entry.is_expired():
                    cache_data[key] = {
                        "value": entry.value,
                        "expires_at": entry.expires_at.isoformat() if entry.expires_at else None,
                        "created_at": entry.created_at.isoformat()
                    }
            
            # Save to file (in a real implementation, use proper file handling)
            pass
            
        except Exception as e:
            # Log error but don't fail
            pass
    
    async def _load_from_disk(self) -> None:
        """Load cache from disk (optional feature)"""
        # This is a simplified implementation
        # In production, you'd want more sophisticated persistence
        try:
            # Load from file (in a real implementation, use proper file handling)
            pass
            
        except Exception as e:
            # Log error but don't fail
            pass


# Global cache manager instance
cache_manager = CacheManager()


def cached(ttl: Optional[int] = None, key_func: Optional[Callable] = None):
    """Decorator for caching function results"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = cache_manager._generate_key((
                    func.__name__,
                    args,
                    tuple(sorted(kwargs.items()))
                ))
            
            # Try to get from cache
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


class FileCache:
    """File-based caching for large data"""
    
    def __init__(self, cache_dir: str = "./cache", max_size: int = 100 * 1024 * 1024):  # 100MB default
        self.cache_dir = Path(cache_dir)
        self.max_size = max_size
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_file_path(self, key: str) -> Path:
        """Get file path for cache key"""
        filename = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{filename}.cache"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from file cache"""
        file_path = self._get_file_path(key)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'rb') as f:
                data = pickle.load(f)
            
            # Check expiration
            if data.get('expires_at') and datetime.fromisoformat(data['expires_at']) < datetime.now():
                file_path.unlink()
                return None
            
            return data['value']
            
        except (pickle.PicklingError, EOFError, json.JSONDecodeError):
            # Corrupted cache file
            if file_path.exists():
                file_path.unlink()
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in file cache"""
        file_path = self._get_file_path(key)
        
        # Check cache size
        self._cleanup_if_needed()
        
        # Prepare data
        data = {
            'value': value,
            'created_at': datetime.now().isoformat()
        }
        
        if ttl:
            data['expires_at'] = (datetime.now() + timedelta(seconds=ttl)).isoformat()
        
        # Write to file
        try:
            with open(file_path, 'wb') as f:
                pickle.dump(data, f)
        except (pickle.PicklingError, OSError):
            # If we can't write, just skip
            if file_path.exists():
                file_path.unlink()
    
    async def delete(self, key: str) -> bool:
        """Delete value from file cache"""
        file_path = self._get_file_path(key)
        
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    
    def _cleanup_if_needed(self) -> None:
        """Clean up cache if it exceeds size limit"""
        total_size = sum(f.stat().st_size for f in self.cache_dir.glob('*.cache'))
        
        if total_size > self.max_size:
            # Delete oldest files
            files = sorted(
                self.cache_dir.glob('*.cache'),
                key=lambda f: f.stat().st_mtime
            )
            
            while total_size > self.max_size * 0.8 and files:  # Clean to 80% of max
                oldest_file = files.pop(0)
                total_size -= oldest_file.stat().st_size
                oldest_file.unlink()
    
    async def clear(self) -> None:
        """Clear all file cache"""
        for cache_file in self.cache_dir.glob('*.cache'):
            cache_file.unlink()


# Global file cache instance
file_cache = FileCache()