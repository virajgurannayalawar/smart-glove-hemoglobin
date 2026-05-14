import cloudinary
import cloudinary.uploader
import cloudinary.utils
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class CloudinaryService:
    def __init__(self):
        if settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY and settings.CLOUDINARY_API_SECRET:
            cloudinary.config(
                cloud_name=settings.CLOUDINARY_CLOUD_NAME,
                api_key=settings.CLOUDINARY_API_KEY,
                api_secret=settings.CLOUDINARY_API_SECRET,
                secure=True
            )
            self.configured = True
        else:
            self.configured = False
            logger.warning("Cloudinary credentials not provided. Storage will fail.")

    def upload_file(self, file_bytes: bytes, public_id: str) -> str:
        """
        Uploads a file to Cloudinary as an authenticated asset (private).
        Returns the public_id.
        """
        if not self.configured:
            raise Exception("Cloudinary is not configured.")
            
        try:
            # Upload the byte array directly
            response = cloudinary.uploader.upload(
                file_bytes,
                public_id=public_id,
                type="authenticated",
                resource_type="image",
                overwrite=True
            )
            return response.get("public_id")
        except Exception as e:
            logger.error(f"Error uploading to Cloudinary: {e}")
            raise e

    def generate_signed_url(self, public_id: str) -> str:
        """
        Generates a signed URL for secure mobile app viewing.
        Only valid with the correct signature.
        """
        if not self.configured or not public_id:
            return ""
            
        try:
            url, options = cloudinary.utils.cloudinary_url(
                public_id,
                type="authenticated",
                sign_url=True
            )
            return url
        except Exception as e:
            logger.error(f"Error generating Cloudinary signed URL: {e}")
            return ""

storage_service = CloudinaryService()
