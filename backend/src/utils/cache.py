"""
File listing cache for remote collections.

This module provides in-memory caching for remote file listings to reduce
API calls to remote storage services (S3, GCS, SMB). Implements collection-aware
TTL based on collection state (Live/Closed/Archived).

Based on research.md Task 3 decision: Use in-memory cache with collection-aware
TTL to achieve 80% API call reduction.
"""

import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional


@dataclass
class CachedFileListing:
    """
    Cached file listing with metadata.

    Stores a list of file paths along with caching metadata (timestamp, TTL)
    to determine when the cache entry has expired.

    Attributes:
        files: List of file paths in the collection
        cached_at: Timestamp when the listing was cached
        ttl_seconds: Time-to-live in seconds before cache expires

    Task: T018 - CachedFileListing dataclass
    """

    files: List[str]
    cached_at: datetime
    ttl_seconds: int

    def is_expired(self) -> bool:
        """
        Check if the cached listing has expired.

        Returns:
            bool: True if cache has expired, False otherwise

        Example:
            >>> cached = CachedFileListing(
            ...     files=['file1.dng', 'file2.dng'],
            ...     cached_at=datetime.utcnow(),
            ...     ttl_seconds=3600
            ... )
            >>> cached.is_expired()
            False
        """
        expiry = self.cached_at + timedelta(seconds=self.ttl_seconds)
        return datetime.utcnow() > expiry

    def time_until_expiry(self) -> timedelta:
        """
        Calculate time remaining until cache expires.

        Returns:
            timedelta: Time until expiry (negative if already expired)
        """
        expiry = self.cached_at + timedelta(seconds=self.ttl_seconds)
        return expiry - datetime.utcnow()


# TTL mapping for collection states (from research.md Task 3)
# Task: T021 - TTL mapping for collection states
COLLECTION_STATE_TTL: Dict[str, int] = {
    "Live": 3600,       # 1 hour (active photography, frequent changes)
    "Closed": 86400,    # 24 hours (infrequent changes)
    "Archived": 604800  # 7 days (infrastructure monitoring only, rarely changes)
}


class FileListingCache:
    """
    In-memory cache for remote collection file listings.

    Provides thread-safe caching of file listings with collection-aware TTL.
    Supports manual invalidation and automatic expiry based on TTL.

    The cache is keyed by collection ID and maintains separate cache entries
    for each collection. Each entry includes the file list, timestamp, and TTL.

    Thread Safety:
        All operations are protected by a threading.Lock to ensure safe
        concurrent access from multiple FastAPI request handlers.

    Performance Target:
        Achieve 80% reduction in API calls to remote storage services
        (research.md NFR1.3).

    Tasks implemented:
        - T019: FileListingCache class with thread-safe operations
        - T020: get(), set(), invalidate(), clear() methods
        - T021: Collection state-aware TTL

    Usage:
        # Initialize cache (singleton in FastAPI app state)
        cache = FileListingCache()

        # Cache a file listing
        cache.set(
            collection_id=1,
            files=['AB3D0001.dng', 'AB3D0002.dng'],
            ttl_seconds=3600
        )

        # Retrieve cached listing
        files = cache.get(collection_id=1)
        if files is None:
            # Cache miss - fetch from remote storage
            files = fetch_from_remote(collection)
            cache.set(collection_id=1, files=files, ttl_seconds=3600)

        # Manual invalidation (e.g., after user refresh)
        cache.invalidate(collection_id=1)
    """

    def __init__(self):
        """
        Initialize the file listing cache.

        Task: T019 - FileListingCache initialization with thread safety
        """
        self._cache: Dict[int, CachedFileListing] = {}
        self._lock = threading.Lock()

    def get(self, collection_id: int) -> Optional[List[str]]:
        """
        Get cached file listing if not expired.

        Args:
            collection_id: ID of the collection

        Returns:
            List[str]: List of file paths if cache hit and not expired
            None: If cache miss or expired

        Thread Safety:
            Protected by lock for safe concurrent access

        Task: T020 - get() method implementation
        """
        with self._lock:
            cached = self._cache.get(collection_id)

            if cached is None:
                # Cache miss
                return None

            if cached.is_expired():
                # Cache expired - remove entry
                del self._cache[collection_id]
                return None

            # Cache hit - return files
            return cached.files

    def set(self, collection_id: int, files: List[str], ttl_seconds: int):
        """
        Store file listing with TTL.

        Args:
            collection_id: ID of the collection
            files: List of file paths to cache
            ttl_seconds: Time-to-live in seconds

        Thread Safety:
            Protected by lock for safe concurrent access

        Example:
            >>> cache = FileListingCache()
            >>> cache.set(
            ...     collection_id=1,
            ...     files=['file1.dng', 'file2.dng'],
            ...     ttl_seconds=COLLECTION_STATE_TTL["Live"]
            ... )

        Task: T020 - set() method implementation
        """
        with self._lock:
            self._cache[collection_id] = CachedFileListing(
                files=files,
                cached_at=datetime.utcnow(),
                ttl_seconds=ttl_seconds
            )

    def invalidate(self, collection_id: int):
        """
        Manually invalidate cache for a collection.

        This is used when the user explicitly requests a cache refresh
        (FR-013a: manual refresh button with cost warning).

        Args:
            collection_id: ID of the collection to invalidate

        Thread Safety:
            Protected by lock for safe concurrent access

        Example:
            # User clicks "Refresh" button
            >>> cache.invalidate(collection_id=1)
            >>> files = fetch_from_remote(collection)
            >>> cache.set(collection_id=1, files=files, ttl_seconds=3600)

        Task: T020 - invalidate() method implementation
        """
        with self._lock:
            self._cache.pop(collection_id, None)

    def clear(self):
        """
        Clear entire cache.

        Useful for testing or memory management. In production, individual
        entries expire based on TTL, so full cache clear is rarely needed.

        Thread Safety:
            Protected by lock for safe concurrent access

        Task: T020 - clear() method implementation
        """
        with self._lock:
            self._cache.clear()

    def get_stats(self) -> Dict[str, int]:
        """
        Get cache statistics for monitoring.

        Returns:
            dict: Statistics including entry count and total files cached

        Example:
            >>> stats = cache.get_stats()
            >>> print(stats)
            {'entries': 10, 'total_files': 150000}
        """
        with self._lock:
            total_files = sum(len(cached.files) for cached in self._cache.values())
            return {
                'entries': len(self._cache),
                'total_files': total_files
            }

    def get_entry_info(self, collection_id: int) -> Optional[Dict]:
        """
        Get detailed information about a cache entry.

        Args:
            collection_id: ID of the collection

        Returns:
            dict: Entry details (file_count, cached_at, ttl, expires_in)
            None: If entry not found

        Example:
            >>> info = cache.get_entry_info(collection_id=1)
            >>> print(info)
            {
                'file_count': 1000,
                'cached_at': '2025-12-29T17:30:00',
                'ttl_seconds': 3600,
                'expires_in_seconds': 2400,
                'is_expired': False
            }
        """
        with self._lock:
            cached = self._cache.get(collection_id)

            if cached is None:
                return None

            time_until_expiry = cached.time_until_expiry()

            return {
                'file_count': len(cached.files),
                'cached_at': cached.cached_at.isoformat(),
                'ttl_seconds': cached.ttl_seconds,
                'expires_in_seconds': int(time_until_expiry.total_seconds()),
                'is_expired': cached.is_expired()
            }


# Singleton instance for dependency injection in FastAPI
_cache_instance: Optional[FileListingCache] = None


def get_file_listing_cache() -> FileListingCache:
    """
    Get or create the singleton FileListingCache instance.

    This function is used as a FastAPI dependency for routes that need
    to access the file listing cache.

    Returns:
        FileListingCache: Singleton instance

    Usage in FastAPI:
        from fastapi import Depends
        from backend.src.utils.cache import get_file_listing_cache

        @app.get("/collections/{id}/files")
        async def list_files(
            id: int,
            cache: FileListingCache = Depends(get_file_listing_cache)
        ):
            cached_files = cache.get(id)
            if cached_files:
                return cached_files
            # Fetch from remote storage...
    """
    global _cache_instance

    if _cache_instance is None:
        _cache_instance = FileListingCache()

    return _cache_instance


def init_file_listing_cache() -> FileListingCache:
    """
    Initialize the file listing cache singleton.

    This should be called during application startup to ensure the cache
    is ready before handling requests.

    Returns:
        FileListingCache: Initialized singleton instance
    """
    global _cache_instance
    _cache_instance = FileListingCache()
    return _cache_instance


def get_ttl_for_state(collection_state: str, custom_ttl: Optional[int] = None) -> int:
    """
    Get TTL (seconds) for a collection based on its state.

    Args:
        collection_state: Collection state ("Live", "Closed", "Archived")
        custom_ttl: Optional custom TTL override

    Returns:
        int: TTL in seconds

    Example:
        >>> get_ttl_for_state("Live")
        3600
        >>> get_ttl_for_state("Closed")
        86400
        >>> get_ttl_for_state("Live", custom_ttl=7200)
        7200

    Task: T021 - TTL selection based on collection state
    """
    if custom_ttl is not None:
        return custom_ttl

    return COLLECTION_STATE_TTL.get(collection_state, COLLECTION_STATE_TTL["Live"])
