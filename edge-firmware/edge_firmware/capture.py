"""
Camera capture module for Smart Glove Edge Firmware.

Captures finger images from Raspberry Pi camera using Picamera2 (modern)
with fallback to raspistill (legacy). Supports hardware variations via config.
"""

import io
import time
import subprocess
from typing import Optional, Tuple
from dataclasses import dataclass

from .config import config


@dataclass
class CaptureResult:
    """Result of a camera capture operation."""
    success: bool
    image_bytes: Optional[bytes] = None
    error: Optional[str] = None
    capture_timestamp: Optional[float] = None
    width: int = 0
    height: int = 0


class CameraCapture:
    """
    Camera capture handler with support for multiple camera backends.
    
    Supports:
    - Picamera2 (modern Raspberry Pi OS)
    - raspistill (legacy Raspberry Pi OS)
    - Mock mode (for development/testing on non-Pi machines)
    """
    
    def __init__(self):
        self.camera = None
        self.backend = None
        self._detect_backend()
    
    def _detect_backend(self) -> None:
        """
        Detect available camera backend.
        
        Tries Picamera2 first, then falls back to raspistill.
        Sets self.backend to 'picamera2', 'raspistill', or 'mock'.
        """
        # Check for mock mode (for development)
        if os.getenv("ENABLE_MOCK_CAMERA", "false").lower() == "true":
            self.backend = "mock"
            return
        
        # Try Picamera2 (modern)
        try:
            from picamera2 import Picamera2
            self.backend = "picamera2"
            return
        except ImportError:
            pass
        
        # Try raspistill (legacy)
        try:
            result = subprocess.run(
                ["raspistill", "--version"],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                self.backend = "raspistill"
                return
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Fall back to mock mode
        self.backend = "mock"
    
    def _capture_with_picamera2(self) -> CaptureResult:
        """
        Capture image using Picamera2 (modern backend).
        
        Returns:
            CaptureResult with image bytes
        """
        try:
            from picamera2 import Picamera2
            
            # Initialize camera
            picam2 = Picamera2()
            
            # Configure camera
            config = picam2.create_still_configuration(
                main={"size": (config.CAMERA_WIDTH, config.CAMERA_HEIGHT)},
                format=config.CAMERA_FORMAT
            )
            picam2.configure(config)
            
            # Start camera
            picam2.start()
            
            # Warm-up time
            time.sleep(config.CAMERA_WARMUP_MS / 1000.0)
            
            # Capture image
            capture_timestamp = time.time()
            frame = picam2.capture_array()
            
            # Stop camera
            picam2.stop()
            picam2.close()
            
            # Convert to bytes
            import cv2
            _, buffer = cv2.imencode(f'.{config.CAMERA_FORMAT}', frame)
            image_bytes = buffer.tobytes()
            
            return CaptureResult(
                success=True,
                image_bytes=image_bytes,
                capture_timestamp=capture_timestamp,
                width=config.CAMERA_WIDTH,
                height=config.CAMERA_HEIGHT
            )
            
        except Exception as e:
            return CaptureResult(
                success=False,
                error=f"Picamera2 capture failed: {str(e)}"
            )
    
    def _capture_with_raspistill(self) -> CaptureResult:
        """
        Capture image using raspistill (legacy backend).
        
        Returns:
            CaptureResult with image bytes
        """
        try:
            capture_timestamp = time.time()
            
            # Build raspistill command
            cmd = [
                "raspistill",
                "-o", "-",  # Output to stdout
                "-w", str(config.CAMERA_WIDTH),
                "-h", str(config.CAMERA_HEIGHT),
                "-e", config.CAMERA_FORMAT.upper(),
                "-t", str(config.CAMERA_WARMUP_MS),  # Warm-up time
                "-n"  # No preview
            ]
            
            # Run command and capture output
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return CaptureResult(
                    success=False,
                    error=f"raspistill failed with code {result.returncode}: {result.stderr.decode()}"
                )
            
            image_bytes = result.stdout
            
            return CaptureResult(
                success=True,
                image_bytes=image_bytes,
                capture_timestamp=capture_timestamp,
                width=config.CAMERA_WIDTH,
                height=config.CAMERA_HEIGHT
            )
            
        except subprocess.TimeoutExpired:
            return CaptureResult(
                success=False,
                error="raspistill capture timed out"
            )
        except Exception as e:
            return CaptureResult(
                success=False,
                error=f"raspistill capture failed: {str(e)}"
            )
    
    def _capture_mock(self) -> CaptureResult:
        """
        Generate mock image for development/testing.
        
        Returns:
            CaptureResult with synthetic image bytes
        """
        try:
            import numpy as np
            import cv2
            
            capture_timestamp = time.time()
            
            # Generate a simple gradient image
            height, width = config.CAMERA_HEIGHT, config.CAMERA_WIDTH
            image = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Create a gradient
            for i in range(height):
                image[i, :] = [i * 255 // height, (height - i) * 255 // height, 128]
            
            # Add some noise to make it look more realistic
            noise = np.random.randint(0, 50, (height, width, 3), dtype=np.uint8)
            image = cv2.add(image, noise)
            
            # Convert to bytes
            _, buffer = cv2.imencode(f'.{config.CAMERA_FORMAT}', image)
            image_bytes = buffer.tobytes()
            
            return CaptureResult(
                success=True,
                image_bytes=image_bytes,
                capture_timestamp=capture_timestamp,
                width=width,
                height=height
            )
            
        except Exception as e:
            return CaptureResult(
                success=False,
                error=f"Mock capture failed: {str(e)}"
            )
    
    def capture(self) -> CaptureResult:
        """
        Capture an image using the detected backend.
        
        Returns:
            CaptureResult with image bytes or error
        """
        if self.backend == "picamera2":
            return self._capture_with_picamera2()
        elif self.backend == "raspistill":
            return self._capture_with_raspistill()
        else:  # mock
            return self._capture_mock()
    
    def get_backend_info(self) -> dict:
        """
        Get information about the current camera backend.
        
        Returns:
            Dictionary with backend information
        """
        return {
            "backend": self.backend,
            "camera_index": config.CAMERA_INDEX,
            "resolution": f"{config.CAMERA_WIDTH}x{config.CAMERA_HEIGHT}",
            "format": config.CAMERA_FORMAT,
            "warmup_ms": config.CAMERA_WARMUP_MS
        }


def capture_finger_image() -> CaptureResult:
    """
    Convenience function to capture a single finger image.
    
    This is the main entry point for camera capture in the firmware.
    
    Returns:
        CaptureResult with image bytes or error
    """
    camera = CameraCapture()
    return camera.capture()


# Import os for mock mode check
import os
