"""
here we are basically defining the three functions
1.connect_to_mongo
2.close_mongo_connection
3.get_database 




"""







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
        # Create unique index on owner_id for users collection, but ignore null/absent owner_id values
        await database.users.create_index(
            "owner_id",
            unique=True,
            partialFilterExpression={"owner_id": {"$exists": True, "$ne": None}},
        )
        await database.users.create_index("glove_api_key", unique=True, sparse=True)
        await database.scan_sessions.create_index("scan_id", unique=True)
        await database.scan_sessions.create_index([("owner_id", 1), ("created_at", -1)])
        await database.scan_sessions.create_index("expires_at")
        await database.scan_events.create_index([("scan_id", 1), ("created_at", 1)])
        await database.scan_events.create_index([("owner_id", 1), ("created_at", -1)])
        await database.devices.create_index([("owner_id", 1), ("device_id", 1)], unique=True)
        await database.devices.create_index([("owner_id", 1), ("last_seen", -1)])
        await database.reports.create_index("report_id", unique=True)
        await database.reports.create_index([("owner_id", 1), ("report_generated_at", -1)])
        await database.reports.create_index([("owner_id", 1), ("reading_id", 1)], unique=True)
        # Create compound index on owner_id and true_timestamp for hemoglobin_readings collection
        await database.hemoglobin_readings.create_index([("owner_id", 1), ("true_timestamp", -1)])
        await database.hemoglobin_readings.create_index([("patient_id", 1), ("true_timestamp", -1)])
        # Create indexes for patients collection
        await database.patients.create_index("owner_id")
        await database.patients.create_index([("owner_id", 1), ("created_at", -1)])
        await database.patients.create_index([("owner_id", 1), ("email", 1)], unique=True)
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
