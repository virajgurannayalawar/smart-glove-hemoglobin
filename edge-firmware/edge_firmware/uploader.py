"""
Backend upload client for Smart Glove Edge Firmware.

Handles multipart upload of encrypted images to the backend with X-Glove-Key authentication.
"""

import json
import time
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
import aiohttp
import asyncio

from .config import config


logger = logging.getLogger(__name__)


@dataclass
class UploadResult:
    """Result of an upload operation."""
    success: bool
    reading_id: Optional[str] = None
    error: Optional[str] = None
    status_code: Optional[int] = None


class Uploader:
    """
    Upload client for sending encrypted images to the backend.
    
    Handles:
    - Multipart form data upload
    - X-Glove-Key authentication
    - Retry logic with exponential backoff
    - Network error handling
    """
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    def _build_upload_url(self, scan_id: str) -> str:
        """Build the full upload URL for a scan session."""
        return config.UPLOAD_ENDPOINT.format(scan_id=scan_id)
    
    def _build_metadata(
        self,
        OwnerId: str,
        PatientId: str,
        IsPregnant: bool,
        CaptureTimestamp: int,
        SyncTimestamp: int
    ) -> str:
        """
        Build metadata JSON matching backend's GloveUploadMetadata schema.
        
        Args:
            OwnerId: Owner ID
            PatientId: Patient ID
            IsPregnant: Whether patient is pregnant
            CaptureTimestamp: Unix timestamp when image was captured
            SyncTimestamp: Unix timestamp when upload started
            
        Returns:
            JSON string of metadata
        """
        metadata = {
            "OwnerId": OwnerId,
            "PatientId": PatientId,
            "CaptureTimestamp": CaptureTimestamp,
            "SyncTimestamp": SyncTimestamp,
            "IsPregnant": IsPregnant
        }
        return json.dumps(metadata)
    
    async def upload(
        self,
        scan_id: str,
        encrypted_image: bytes,
        OwnerId: str,
        PatientId: str,
        IsPregnant: bool,
        CaptureTimestamp: int,
        SyncTimestamp: int
    ) -> UploadResult:
        """
        Upload encrypted image to backend.
        
        Args:
            scan_id: Scan session ID
            encrypted_image: AES-256 encrypted image bytes (IV + ciphertext)
            OwnerId: Owner ID
            PatientId: Patient ID
            IsPregnant: Whether patient is pregnant
            CaptureTimestamp: Unix timestamp when image was captured
            SyncTimestamp: Unix timestamp when upload started
            
        Returns:
            UploadResult with success status and reading_id or error
        """
        url = self._build_upload_url(scan_id)
        metadata = self._build_metadata(
            OwnerId, PatientId, IsPregnant, CaptureTimestamp, SyncTimestamp
        )
        
        logger.info(f"Uploading to {url}")
        logger.debug(f"Metadata: {metadata}")
        logger.debug(f"Encrypted image size: {len(encrypted_image)} bytes")
        
        # Prepare multipart form data
        data = aiohttp.FormData()
        data.add_field(
            'image',
            encrypted_image,
            filename='image.bin',
            content_type='application/octet-stream'
        )
        data.add_field(
            'metadata',
            metadata,
            content_type='application/json'
        )
        
        # Prepare headers
        headers = {
            'X-Glove-Key': config.GLOVE_API_KEY
        }
        
        session = await self._get_session()
        
        try:
            async with session.post(url, data=data, headers=headers) as response:
                status_code = response.status
                response_text = await response.text()
                
                logger.info(f"Upload response status: {status_code}")
                
                if status_code == 200:
                    response_data = await response.json()
                    reading_id = response_data.get('reading_id')
                    logger.info(f"Upload successful, reading_id: {reading_id}")
                    return UploadResult(
                        success=True,
                        reading_id=reading_id,
                        status_code=status_code
                    )
                else:
                    error_msg = f"Upload failed with status {status_code}: {response_text}"
                    logger.error(error_msg)
                    return UploadResult(
                        success=False,
                        error=error_msg,
                        status_code=status_code
                    )
                    
        except aiohttp.ClientError as e:
            error_msg = f"Network error during upload: {str(e)}"
            logger.error(error_msg)
            return UploadResult(
                success=False,
                error=error_msg,
                status_code=None
            )
        except asyncio.TimeoutError:
            error_msg = "Upload timed out"
            logger.error(error_msg)
            return UploadResult(
                success=False,
                error=error_msg,
                status_code=None
            )
        except Exception as e:
            error_msg = f"Unexpected error during upload: {str(e)}"
            logger.exception(error_msg)
            return UploadResult(
                success=False,
                error=error_msg,
                status_code=None
            )
    
    async def upload_with_retry(
        self,
        scan_id: str,
        encrypted_image: bytes,
        OwnerId: str,
        PatientId: str,
        IsPregnant: bool,
        CaptureTimestamp: int,
        SyncTimestamp: int,
        max_attempts: int = None,
        base_backoff: int = None
    ) -> UploadResult:
        """
        Upload with automatic retry on failure.
        
        Uses exponential backoff with jitter for retries.
        
        Args:
            scan_id: Scan session ID
            encrypted_image: AES-256 encrypted image bytes
            OwnerId: Owner ID
            PatientId: Patient ID
            IsPregnant: Whether patient is pregnant
            CaptureTimestamp: Unix timestamp when image was captured
            SyncTimestamp: Unix timestamp when upload started
            max_attempts: Maximum retry attempts (defaults to config.RETRY_MAX_ATTEMPTS)
            base_backoff: Base backoff time in seconds (defaults to config.RETRY_BACKOFF_SECONDS)
            
        Returns:
            UploadResult with success status and reading_id or error
        """
        max_attempts = max_attempts or config.RETRY_MAX_ATTEMPTS
        base_backoff = base_backoff or config.RETRY_BACKOFF_SECONDS
        
        last_error = None
        
        for attempt in range(1, max_attempts + 1):
            logger.info(f"Upload attempt {attempt}/{max_attempts}")
            
            result = await self.upload(
                scan_id=scan_id,
                encrypted_image=encrypted_image,
                OwnerId=OwnerId,
                PatientId=PatientId,
                IsPregnant=IsPregnant,
                CaptureTimestamp=CaptureTimestamp,
                SyncTimestamp=SyncTimestamp
            )
            
            if result.success:
                return result
            
            last_error = result.error
            
            # Don't retry on client errors (4xx)
            if result.status_code and 400 <= result.status_code < 500:
                logger.warning(f"Client error {result.status_code}, not retrying")
                return result
            
            # Retry on server errors (5xx) and network errors
            if attempt < max_attempts:
                # Exponential backoff with jitter
                backoff = base_backoff * (2 ** (attempt - 1))
                jitter = backoff * 0.1 * (time.time() % 1)  # 10% jitter
                total_backoff = backoff + jitter
                
                logger.info(f"Retrying in {total_backoff:.1f} seconds...")
                await asyncio.sleep(total_backoff)
        
        # All attempts failed
        error_msg = f"Upload failed after {max_attempts} attempts. Last error: {last_error}"
        logger.error(error_msg)
        return UploadResult(
            success=False,
            error=error_msg,
            status_code=None
        )
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()


# Convenience function for single upload
async def upload_to_backend(
    scan_id: str,
    encrypted_image: bytes,
    OwnerId: str,
    PatientId: str,
    IsPregnant: bool,
    CaptureTimestamp: int,
    SyncTimestamp: int
) -> UploadResult:
    """
    Convenience function to upload encrypted image to backend with retry.
    
    This is the main entry point for uploads in the firmware.
    
    Args:
        scan_id: Scan session ID
        encrypted_image: AES-256 encrypted image bytes
        OwnerId: Owner ID
        PatientId: Patient ID
        IsPregnant: Whether patient is pregnant
        CaptureTimestamp: Unix timestamp when image was captured
        SyncTimestamp: Unix timestamp when upload started
        
    Returns:
        UploadResult with success status and reading_id or error
    """
    uploader = Uploader()
    try:
        return await uploader.upload_with_retry(
            scan_id=scan_id,
            encrypted_image=encrypted_image,
            OwnerId=OwnerId,
            PatientId=PatientId,
            IsPregnant=IsPregnant,
            CaptureTimestamp=CaptureTimestamp,
            SyncTimestamp=SyncTimestamp
        )
    finally:
        await uploader.close()
