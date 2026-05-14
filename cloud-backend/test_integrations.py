import asyncio
import logging
from app.services.db import connect_to_mongo, close_mongo_connection, db
from app.services.cloudinary_service import storage_service
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_mongodb():
    logger.info("Testing MongoDB...")
    try:
        await connect_to_mongo()
        database = db.client[settings.DATABASE_NAME]
        # Try a simple ping command
        await db.client.admin.command('ping')
        logger.info("MongoDB ping successful!")
        
        # Test collections
        collections = await database.list_collection_names()
        logger.info(f"Available collections: {collections}")
        
        await close_mongo_connection()
        return True
    except Exception as e:
        logger.error(f"MongoDB test failed: {e}")
        return False

def test_cloudinary():
    logger.info("Testing Cloudinary...")
    try:
        if not storage_service.configured:
            logger.error("Cloudinary is not configured!")
            return False
            
        # Create a simple 1x1 transparent PNG in bytes
        test_image_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0bIDAT\x08\xd7c\x60\x00\x02\x00\x00\x05\x00\x01\xe2+\xfe\x0b\x00\x00\x00\x00IEND\xaeB`\x82'
        
        logger.info("Uploading test image...")
        public_id = storage_service.upload_file(test_image_bytes, "test_connection_image")
        logger.info(f"Upload successful. Public ID: {public_id}")
        
        signed_url = storage_service.generate_signed_url(public_id)
        logger.info(f"Generated signed URL: {signed_url}")
        
        return True
    except Exception as e:
        logger.error(f"Cloudinary test failed: {e}")
        return False

async def main():
    mongo_ok = await test_mongodb()
    cloudinary_ok = test_cloudinary()
    
    print("\n--- Summary ---")
    print(f"MongoDB Integration: {'WORKING' if mongo_ok else 'FAILED'}")
    print(f"Cloudinary Integration: {'WORKING' if cloudinary_ok else 'FAILED'}")

if __name__ == "__main__":
    asyncio.run(main())
