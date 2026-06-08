"""
Configuration module for Smart Glove Edge Firmware.

Loads configuration from environment variables and provides a centralized config object.
Hardware variations (camera index, GPIO pins, etc.) are handled via .env file.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Centralized configuration for the edge firmware."""
    
    # Backend Configuration
    BACKEND_BASE_URL: str = os.getenv("BACKEND_BASE_URL", "https://api.smartglovecloud.com")
    API_PREFIX: str = os.getenv("API_PREFIX", "/api/v1")
    
    @property
    def UPLOAD_ENDPOINT(self) -> str:
        """Full upload endpoint URL template."""
        return f"{self.BACKEND_BASE_URL}{self.API_PREFIX}/scan/sessions/{{scan_id}}/upload"
    
    # Camera Configuration
    CAMERA_INDEX: int = int(os.getenv("CAMERA_INDEX", "0"))
    CAMERA_RESOLUTION: str = os.getenv("CAMERA_RESOLUTION", "1024x1024")
    CAMERA_FORMAT: str = os.getenv("CAMERA_FORMAT", "jpeg")
    CAMERA_WARMUP_MS: int = int(os.getenv("CAMERA_WARMUP_MS", "300"))
    
    @property
    def CAMERA_WIDTH(self) -> int:
        """Extract width from resolution string (e.g., '1024x1024' -> 1024)."""
        return int(self.CAMERA_RESOLUTION.split("x")[0])
    
    @property
    def CAMERA_HEIGHT(self) -> int:
        """Extract height from resolution string (e.g., '1024x1024' -> 1024)."""
        return int(self.CAMERA_RESOLUTION.split("x")[1])
    
    # Network Configuration
    SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))
    MDNS_HOSTNAME: str = os.getenv("MDNS_HOSTNAME", "glove")
    
    # Provisioning Configuration
    OWNER_ID: Optional[str] = os.getenv("OWNER_ID")
    GLOVE_API_KEY: Optional[str] = os.getenv("GLOVE_API_KEY")
    
    # Power Management
    ENABLE_GPIO_POWER_CONTROL: bool = os.getenv("ENABLE_GPIO_POWER_CONTROL", "false").lower() == "true"
    GPIO_CAMERA_POWER_PIN: int = int(os.getenv("GPIO_CAMERA_POWER_PIN", "17"))
    GPIO_LED_POWER_PIN: int = int(os.getenv("GPIO_LED_POWER_PIN", "18"))
    
    # Cache Configuration
    CACHE_DIR: Path = Path(os.getenv("CACHE_DIR", "/var/lib/smart_glove/queue"))
    MAX_CACHE_SIZE_MB: int = int(os.getenv("MAX_CACHE_SIZE_MB", "100"))
    RETRY_MAX_ATTEMPTS: int = int(os.getenv("RETRY_MAX_ATTEMPTS", "5"))
    RETRY_BACKOFF_SECONDS: int = int(os.getenv("RETRY_BACKOFF_SECONDS", "30"))
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")
    
    # Encryption Configuration (must match backend)
    AES_SECRET_KEY: str = os.getenv("AES_SECRET_KEY", "32byte-long-secret-key-for-aes-!")[:32]
    
    def validate(self) -> bool:
        """Validate that required configuration is present."""
        if not self.OWNER_ID:
            raise ValueError("OWNER_ID must be set in environment or .env file")
        if not self.GLOVE_API_KEY:
            raise ValueError("GLOVE_API_KEY must be set in environment or .env file")
        if len(self.AES_SECRET_KEY) != 32:
            raise ValueError("AES_SECRET_KEY must be exactly 32 bytes")
        return True
    
    def ensure_cache_dir(self) -> Path:
        """Ensure cache directory exists."""
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        return self.CACHE_DIR


# Global config instance
config = Config()
