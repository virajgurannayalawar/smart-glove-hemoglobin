from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None

db = Database()

async def connect_to_mongo():
    logger.info("Connecting to MongoDB...")
    db.client = AsyncIOMotorClient(settings.MONGODB_URL)
    
    # Initialize indexes
    database = db.client[settings.DATABASE_NAME]
    try:
        # Create unique index on patient_id for users collection
        await database.users.create_index("patient_id", unique=True)
        # Create compound index on patient_id and true_timestamp for history collection
        await database.history.create_index([("patient_id", 1), ("true_timestamp", -1)])
        logger.info("MongoDB connection and indexing successful.")
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB indexes: {e}")

async def close_mongo_connection():
    logger.info("Closing MongoDB connection...")
    if db.client:
        db.client.close()
        logger.info("MongoDB connection closed.")

def get_database():
    return db.client[settings.DATABASE_NAME]
