from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Smart Glove Backend"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "supersecretkey-please-change-in-production"
    ALGORITHM: str = "HS256"
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
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
