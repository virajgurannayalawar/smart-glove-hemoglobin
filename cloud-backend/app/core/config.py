from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal
from pydantic import Field, field_validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "Smart Glove Backend"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "supersecretkey-please-change-in-production"
    ALGORITHM: str = "HS256"

    """
       7-Day JWT Authentication ✅

       60 * 24 * 7 (10,080 minutes = 7 days)
    """

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days 
    
    # AES Encryption for image payload
    AES_SECRET_KEY: str = "32byte-long-secret-key-for-aes-!" # Must be exactly 32 bytes for AES-256
    
    # Database
    MONGODB_URL: str = "mongodb://localhost:27017" # Replace with MongoDB Atlas URI
    DATABASE_NAME: str = "smart_glove"
    
    # Cloudinary S3 Replacement
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    # Model integration
    MODEL_PROVIDER: Literal["mock", "pytorch"] = "pytorch"
    MODEL_PATH: str = "app/services/hb_predictor.pth"
    MOCK_HEMOGLOBIN_VALUE: float = 13.2

    # Image processing (pre-model)
    IMAGE_PROCESSING_ENABLED: bool = True
    MODEL_IMAGE_SIZE: int = 224

    # Observability
    LOG_LEVEL: str = "INFO"

    # CORS
    CORS_ALLOW_ORIGINS: list[str] = Field(default_factory=lambda: ["*"])
    CORS_ALLOW_METHODS: list[str] = Field(default_factory=lambda: ["*"])
    CORS_ALLOW_HEADERS: list[str] = Field(default_factory=lambda: ["*"])
    
    @field_validator("DATABASE_NAME", mode="before")
    def _strip_database_name_quotes(cls, v):
        if isinstance(v, str):
            return v.strip().strip('"').strip("'")
        return v

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
