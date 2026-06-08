"""
Offline cache and retry module for Smart Glove Edge Firmware.

Provides disk-based queue for failed uploads with background retry worker.
Handles atomic writes, exponential backoff, and cache size management.
"""

import os
import json
import time
import uuid
import logging
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime

from .config import config


logger = logging.getLogger(__name__)


@dataclass
class CacheItem:
    """Represents a cached upload item."""
    item_id: str
    scan_id: str
    encrypted_image_path: str
    metadata: Dict[str, Any]
    created_at: float
    attempt_count: int = 0
    last_attempt_at: Optional[float] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheItem':
        """Create from dictionary."""
        return cls(**data)


class CacheManager:
    """
    Manages the offline cache queue.
    
    Provides atomic writes, size management, and item retrieval.
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or config.CACHE_DIR
        self.max_size_mb = config.MAX_CACHE_SIZE_MB
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self) -> None:
        """Ensure cache directory exists."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_item_dir(self, item_id: str) -> Path:
        """Get directory path for a cache item."""
        return self.cache_dir / item_id
    
    def _get_metadata_path(self, item_id: str) -> Path:
        """Get metadata file path for a cache item."""
        return self._get_item_dir(item_id) / "metadata.json"
    
    def _get_image_path(self, item_id: str) -> Path:
        """Get encrypted image file path for a cache item."""
        return self._get_item_dir(item_id) / "image.enc"
    
    def _get_temp_image_path(self, item_id: str) -> Path:
        """Get temporary image file path for atomic write."""
        return self._get_item_dir(item_id) / "image.enc.tmp"
    
    def get_cache_size_mb(self) -> float:
        """Get current cache size in megabytes."""
        total_bytes = 0
        for item_dir in self.cache_dir.iterdir():
            if item_dir.is_dir():
                for file in item_dir.iterdir():
                    if file.is_file():
                        total_bytes += file.stat().st_size
        return total_bytes / (1024 * 1024)
    
    def is_cache_full(self) -> bool:
        """Check if cache has reached size limit."""
        return self.get_cache_size_mb() >= self.max_size_mb
    
    def add_item(
        self,
        scan_id: str,
        encrypted_image: bytes,
        metadata: Dict[str, Any]
    ) -> Optional[CacheItem]:
        """
        Add an item to the cache.
        
        Args:
            scan_id: Scan session ID
            encrypted_image: Encrypted image bytes
            metadata: Upload metadata
            
        Returns:
            CacheItem if successful, None if cache is full
        """
        if self.is_cache_full():
            logger.warning("Cache is full, cannot add item")
            return None
        
        item_id = str(uuid.uuid4())
        item_dir = self._get_item_dir(item_id)
        
        try:
            # Create item directory
            item_dir.mkdir(exist_ok=True)
            
            # Write encrypted image atomically
            temp_image_path = self._get_temp_image_path(item_id)
            with open(temp_image_path, 'wb') as f:
                f.write(encrypted_image)
                f.flush()
                os.fsync(f.fileno())
            
            # Rename to final path (atomic on POSIX)
            temp_image_path.rename(self._get_image_path(item_id))
            
            # Write metadata
            cache_item = CacheItem(
                item_id=item_id,
                scan_id=scan_id,
                encrypted_image_path=str(self._get_image_path(item_id)),
                metadata=metadata,
                created_at=time.time(),
                attempt_count=0
            )
            
            metadata_path = self._get_metadata_path(item_id)
            with open(metadata_path, 'w') as f:
                json.dump(cache_item.to_dict(), f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            
            logger.info(f"Added item {item_id} to cache (scan_id: {scan_id})")
            return cache_item
            
        except Exception as e:
            logger.error(f"Failed to add item to cache: {e}")
            # Cleanup on failure
            if item_dir.exists():
                self._remove_item(item_id)
            return None
    
    def get_item(self, item_id: str) -> Optional[CacheItem]:
        """
        Retrieve a cache item by ID.
        
        Args:
            item_id: Item ID
            
        Returns:
            CacheItem if found, None otherwise
        """
        metadata_path = self._get_metadata_path(item_id)
        if not metadata_path.exists():
            return None
        
        try:
            with open(metadata_path, 'r') as f:
                data = json.load(f)
            return CacheItem.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to read cache item {item_id}: {e}")
            return None
    
    def get_all_items(self) -> List[CacheItem]:
        """
        Get all cached items, sorted by creation time (oldest first).
        
        Returns:
            List of CacheItems
        """
        items = []
        for item_dir in self.cache_dir.iterdir():
            if item_dir.is_dir():
                item_id = item_dir.name
                item = self.get_item(item_id)
                if item:
                    items.append(item)
        
        # Sort by creation time (oldest first)
        items.sort(key=lambda x: x.created_at)
        return items
    
    def update_item(self, item: CacheItem) -> bool:
        """
        Update a cache item's metadata.
        
        Args:
            item: CacheItem with updated fields
            
        Returns:
            True if successful, False otherwise
        """
        metadata_path = self._get_metadata_path(item.item_id)
        if not metadata_path.exists():
            return False
        
        try:
            with open(metadata_path, 'w') as f:
                json.dump(item.to_dict(), f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            return True
        except Exception as e:
            logger.error(f"Failed to update cache item {item.item_id}: {e}")
            return False
    
    def _remove_item(self, item_id: str) -> None:
        """
        Remove a cache item from disk.
        
        Args:
            item_id: Item ID to remove
        """
        item_dir = self._get_item_dir(item_id)
        try:
            if item_dir.exists():
                for file in item_dir.iterdir():
                    file.unlink()
                item_dir.rmdir()
                logger.info(f"Removed cache item {item_id}")
        except Exception as e:
            logger.error(f"Failed to remove cache item {item_id}: {e}")
    
    def remove_item(self, item_id: str) -> bool:
        """
        Public method to remove a cache item.
        
        Args:
            item_id: Item ID to remove
            
        Returns:
            True if successful, False otherwise
        """
        self._remove_item(item_id)
        return not self._get_item_dir(item_id).exists()
    
    def get_encrypted_image(self, item: CacheItem) -> Optional[bytes]:
        """
        Read encrypted image bytes from disk.
        
        Args:
            item: CacheItem
            
        Returns:
            Image bytes if successful, None otherwise
        """
        try:
            with open(item.encrypted_image_path, 'rb') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read encrypted image for item {item.item_id}: {e}")
            return None
    
    def cleanup_old_items(self, max_age_hours: int = 24) -> int:
        """
        Remove items older than max_age_hours.
        
        Args:
            max_age_hours: Maximum age in hours
            
        Returns:
            Number of items removed
        """
        cutoff_time = time.time() - (max_age_hours * 3600)
        items = self.get_all_items()
        removed = 0
        
        for item in items:
            if item.created_at < cutoff_time:
                self._remove_item(item.item_id)
                removed += 1
        
        if removed > 0:
            logger.info(f"Cleaned up {removed} old cache items")
        
        return removed


class CacheWorker:
    """
    Background worker for retrying cached uploads.
    
    Processes the cache queue with exponential backoff and throttling.
    """
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        self.cache_manager = cache_manager or CacheManager()
        self.upload_delay = 5.0  # Seconds between uploads (throttling)
    
    async def _retry_item(self, item: CacheItem) -> bool:
        """
        Retry a single cached upload.
        
        Args:
            item: CacheItem to retry
            
        Returns:
            True if successful, False otherwise
        """
        from .uploader import upload_to_backend
        
        logger.info(f"Retrying cached item {item.item_id} (attempt {item.attempt_count + 1})")
        
        # Read encrypted image
        encrypted_image = self.cache_manager.get_encrypted_image(item)
        if not encrypted_image:
            logger.error(f"Failed to read encrypted image for item {item.item_id}")
            return False
        
        # Update attempt count
        item.attempt_count += 1
        item.last_attempt_at = time.time()
        self.cache_manager.update_item(item)
        
        # Calculate backoff delay
        backoff = config.RETRY_BACKOFF_SECONDS * (2 ** (item.attempt_count - 1))
        await asyncio.sleep(backoff)
        
        # Attempt upload
        try:
            result = await upload_to_backend(
                scan_id=item.scan_id,
                encrypted_image=encrypted_image,
                OwnerId=item.metadata.get("OwnerId"),
                PatientId=item.metadata.get("PatientId"),
                IsPregnant=item.metadata.get("IsPregnant", False),
                CaptureTimestamp=item.metadata.get("CaptureTimestamp"),
                SyncTimestamp=item.metadata.get("SyncTimestamp")
            )
            
            if result.success:
                logger.info(f"Successfully uploaded cached item {item.item_id}")
                self.cache_manager.remove_item(item.item_id)
                return True
            else:
                logger.warning(f"Upload failed for cached item {item.item_id}: {result.error}")
                item.error = result.error
                self.cache_manager.update_item(item)
                
                # Remove if max attempts reached
                if item.attempt_count >= config.RETRY_MAX_ATTEMPTS:
                    logger.error(f"Max attempts reached for item {item.item_id}, removing")
                    self.cache_manager.remove_item(item.item_id)
                
                return False
                
        except Exception as e:
            logger.error(f"Exception during retry of item {item.item_id}: {e}")
            item.error = str(e)
            self.cache_manager.update_item(item)
            return False
    
    async def run(self, shutdown_event: asyncio.Event):
        """
        Main run loop for the cache worker.
        
        Processes cached items until shutdown event is set.
        
        Args:
            shutdown_event: Asyncio event to signal shutdown
        """
        logger.info("Cache worker started")
        
        while not shutdown_event.is_set():
            try:
                # Cleanup old items
                self.cache_manager.cleanup_old_items()
                
                # Get all cached items
                items = self.cache_manager.get_all_items()
                
                if not items:
                    logger.debug("No cached items to process")
                    await asyncio.sleep(30)  # Wait before checking again
                    continue
                
                logger.info(f"Processing {len(items)} cached items")
                
                # Process items one by one
                for item in items:
                    if shutdown_event.is_set():
                        break
                    
                    await self._retry_item(item)
                    
                    # Throttle uploads
                    if not shutdown_event.is_set():
                        await asyncio.sleep(self.upload_delay)
                
                # Wait before next cycle
                if not shutdown_event.is_set():
                    await asyncio.sleep(60)
                    
            except Exception as e:
                logger.exception(f"Cache worker error: {e}")
                await asyncio.sleep(30)
        
        logger.info("Cache worker stopped")


def add_to_cache(
    scan_id: str,
    encrypted_image: bytes,
    metadata: Dict[str, Any]
) -> Optional[CacheItem]:
    """
    Convenience function to add an item to the cache.
    
    Args:
        scan_id: Scan session ID
        encrypted_image: Encrypted image bytes
        metadata: Upload metadata
        
    Returns:
        CacheItem if successful, None if cache is full
    """
    cache_manager = CacheManager()
    return cache_manager.add_item(scan_id, encrypted_image, metadata)
