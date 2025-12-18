"""
Caching system for processed file results
"""
import os
import sys
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import OrderedDict
from threading import Lock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.logger import get_system_logger
from config import Config

logger = get_system_logger()


class FileCache:
    """
    In-memory cache for processed file results with LRU eviction.
    """
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        """
        Initialize file cache.
        
        Args:
            max_size: Maximum number of cached items
            ttl_seconds: Time-to-live in seconds (default: 1 hour)
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self.lock = Lock()
        logger.info("File cache initialized", max_size=max_size, ttl_seconds=ttl_seconds)
    
    def _is_expired(self, cached_item: Dict[str, Any]) -> bool:
        """Check if cached item has expired."""
        if 'timestamp' not in cached_item:
            return True
        
        cached_time = datetime.fromisoformat(cached_item['timestamp'])
        age = (datetime.now() - cached_time).total_seconds()
        return age > self.ttl_seconds
    
    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Get cached result.
        
        Args:
            cache_key: Cache key (file hash or file_id)
            
        Returns:
            Cached result or None if not found/expired
        """
        with self.lock:
            if cache_key not in self.cache:
                return None
            
            cached_item = self.cache[cache_key]
            
            # Check if expired
            if self._is_expired(cached_item):
                del self.cache[cache_key]
                logger.debug("Cache entry expired", key=cache_key)
                return None
            
            # Move to end (most recently used)
            self.cache.move_to_end(cache_key)
            
            logger.debug("Cache hit", key=cache_key)
            return cached_item.get('result')
    
    def set(self, cache_key: str, result: Dict[str, Any]) -> None:
        """
        Store result in cache.
        
        Args:
            cache_key: Cache key (file hash or file_id)
            result: Processing result to cache
        """
        with self.lock:
            # Remove if exists (to update position)
            if cache_key in self.cache:
                del self.cache[cache_key]
            
            # Evict oldest if at capacity
            if len(self.cache) >= self.max_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                logger.debug("Cache evicted oldest entry", key=oldest_key)
            
            # Store new entry
            self.cache[cache_key] = {
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.debug("Cache entry stored", key=cache_key, cache_size=len(self.cache))
    
    def clear(self) -> None:
        """Clear all cached entries."""
        with self.lock:
            self.cache.clear()
            logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'ttl_seconds': self.ttl_seconds,
                'keys': list(self.cache.keys())
            }


class ResultCache:
    """
    Result caching system that combines in-memory cache with database lookup.
    """
    
    def __init__(
        self,
        embedding_db=None,
        enable_memory_cache: bool = True,
        enable_db_cache: bool = True,
        memory_cache_size: int = 100,
        memory_cache_ttl: int = 3600
    ):
        """
        Initialize result cache.
        
        Args:
            embedding_db: EmbeddingDatabase instance for database cache lookup
            enable_memory_cache: Enable in-memory caching
            enable_db_cache: Enable database cache lookup
            memory_cache_size: Maximum in-memory cache size
            memory_cache_ttl: In-memory cache TTL in seconds
        """
        self.embedding_db = embedding_db
        self.enable_memory_cache = enable_memory_cache
        self.enable_db_cache = enable_db_cache
        
        if enable_memory_cache:
            self.memory_cache = FileCache(max_size=memory_cache_size, ttl_seconds=memory_cache_ttl)
        else:
            self.memory_cache = None
        
        logger.info("Result cache initialized",
                   memory_cache=enable_memory_cache,
                   db_cache=enable_db_cache)
    
    def _compute_file_hash(self, file_path: str) -> str:
        """
        Compute SHA256 hash of file for cache key.
        
        Args:
            file_path: Path to file
            
        Returns:
            SHA256 hash as hex string
        """
        sha256_hash = hashlib.sha256()
        
        try:
            with open(file_path, "rb") as f:
                # Read file in chunks to handle large files
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error("Failed to compute file hash", file_path=file_path, error=str(e))
            # Fallback to filename-based hash
            return hashlib.sha256(os.path.basename(file_path).encode()).hexdigest()
    
    def _get_cache_key(self, file_path: str, file_id: Optional[str] = None) -> str:
        """
        Get cache key for file.
        
        Args:
            file_path: Path to file
            file_id: Optional file ID (if available)
            
        Returns:
            Cache key string
        """
        if file_id:
            return f"file_id:{file_id}"
        
        # Use file hash as cache key
        file_hash = self._compute_file_hash(file_path)
        return f"file_hash:{file_hash}"
    
    def get_cached_result(
        self,
        file_path: str,
        file_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached result for file.
        
        Checks in-memory cache first, then database.
        
        Args:
            file_path: Path to file
            file_id: Optional file ID
            
        Returns:
            Cached result or None if not found
        """
        cache_key = self._get_cache_key(file_path, file_id)
        
        # Check in-memory cache first
        if self.enable_memory_cache and self.memory_cache:
            cached_result = self.memory_cache.get(cache_key)
            if cached_result:
                logger.info("Cache hit (memory)", file_path=file_path)
                return cached_result
        
        # Check database cache
        if self.enable_db_cache and self.embedding_db:
            try:
                # Try to get by file_id if available
                if file_id:
                    db_result = self.embedding_db.get_by_file_id(file_id)
                else:
                    # Use file hash to look up in database
                    # Note: This requires storing file_hash in database metadata
                    # For now, we'll use file_id lookup
                    file_hash = self._compute_file_hash(file_path)
                    # Try to find by file_name match (fallback)
                    db_result = None
                
                if db_result:
                    # Convert database record to result format
                    result = self._db_record_to_result(db_result)
                    
                    # Store in memory cache for faster future access
                    if self.enable_memory_cache and self.memory_cache:
                        self.memory_cache.set(cache_key, result)
                    
                    logger.info("Cache hit (database)", file_path=file_path, file_id=file_id)
                    return result
            except Exception as e:
                logger.warning("Database cache lookup failed", error=str(e))
        
        logger.debug("Cache miss", file_path=file_path)
        return None
    
    def _db_record_to_result(self, db_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert database record to processing result format.
        
        Args:
            db_record: Database record from embedding database
            
        Returns:
            Processing result dictionary
        """
        try:
            result = {
                'file_name': db_record.get('file_name', ''),
                'file_id': db_record.get('file_id', ''),
                'modality': db_record.get('modality', ''),
                'category': db_record.get('category', ''),
                'raw_text': db_record.get('raw_text', ''),
                'visual_features': db_record.get('visual_features', ''),
                'labels': db_record.get('labels', {}),
                'quality_score': db_record.get('quality_score', 0.0),
                'quality_status': 'high' if db_record.get('quality_score', 0) >= 0.8 else 'medium' if db_record.get('quality_score', 0) >= 0.6 else 'low',
                'confidence': db_record.get('metadata', {}).get('confidence', 0.0),
                'success': True,
                'cached': True,  # Mark as cached result
                'cached_at': db_record.get('updated_at', datetime.now().isoformat()),
                'processing_time': db_record.get('processing_time', 0.0)
            }
            
            # Add metadata if available
            if db_record.get('metadata'):
                result['processing_metadata'] = db_record['metadata']
            
            return result
        except Exception as e:
            logger.error("Failed to convert DB record to result", error=str(e))
            return None
    
    def store_result(
        self,
        file_path: str,
        result: Dict[str, Any],
        file_id: Optional[str] = None
    ) -> None:
        """
        Store result in cache.
        
        Args:
            file_path: Path to file
            result: Processing result to cache
            file_id: Optional file ID
        """
        cache_key = self._get_cache_key(file_path, file_id)
        
        # Store in memory cache
        if self.enable_memory_cache and self.memory_cache:
            self.memory_cache.set(cache_key, result)
            logger.debug("Result stored in memory cache", file_path=file_path)
        
        # Database storage is handled by embedding_db.store_embedding()
        # We just ensure the result is marked as not cached
        if 'cached' in result:
            result['cached'] = False
    
    def clear_cache(self) -> None:
        """Clear all caches."""
        if self.enable_memory_cache and self.memory_cache:
            self.memory_cache.clear()
        logger.info("All caches cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {
            'memory_cache_enabled': self.enable_memory_cache,
            'db_cache_enabled': self.enable_db_cache
        }
        
        if self.enable_memory_cache and self.memory_cache:
            stats['memory_cache'] = self.memory_cache.get_stats()
        
        return stats

