import boto3
from botocore.exceptions import ClientError
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class S3Service:
    def __init__(self):
        # We initialize the client if credentials are provided
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            self.s3_client = boto3.client(
                's3',
                region_name=settings.AWS_REGION_NAME,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
            self.bucket_name = settings.AWS_BUCKET_NAME
        else:
            self.s3_client = None
            logger.warning("AWS credentials not provided. S3 service will not function properly.")

    def upload_file(self, file_bytes: bytes, object_key: str, content_type: str = "image/jpeg") -> str:
        """
        Uploads a file to S3 and returns the object key.
        The file is stored with Server-Side Encryption (SSE-S3).
        """
        if not self.s3_client:
            raise Exception("S3 client is not initialized.")
            
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=file_bytes,
                ContentType=content_type,
                ServerSideEncryption='AES256' # Explicitly request SSE-S3
            )
            return object_key
        except ClientError as e:
            logger.error(f"Error uploading to S3: {e}")
            raise e

    def generate_presigned_url(self, object_key: str, expiration: int = 900) -> str:
        """
        Generates a short-lived presigned URL for secure mobile app viewing.
        Default expiration is 15 minutes (900 seconds).
        """
        if not self.s3_client:
            return ""
            
        try:
            response = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': object_key
                },
                ExpiresIn=expiration
            )
            return response
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {e}")
            return ""

s3_service = S3Service()
