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
        # Create unique index on OwnerId for users collection, but ignore null/absent OwnerId values.
        # Use $type string so the index only applies to actual OwnerId string values.
        await database.users.create_index(
            "OwnerId",
            unique=True,
            partialFilterExpression={"OwnerId": {"$type": "string"}},
        )
        await database.users.create_index("GloveApiKey", unique=True, sparse=True)
        await database.scan_sessions.create_index("ScanId", unique=True)
        await database.scan_sessions.create_index([("OwnerId", 1), ("CreatedAt", -1)])
        await database.scan_sessions.create_index("ExpiresAt")
        await database.scan_events.create_index([("ScanId", 1), ("CreatedAt", 1)])
        await database.scan_events.create_index([("OwnerId", 1), ("CreatedAt", -1)])
        await database.devices.create_index([("OwnerId", 1), ("DeviceId", 1)], unique=True)
        await database.devices.create_index([("OwnerId", 1), ("LastSeen", -1)])
        await database.reports.create_index("ReportId", unique=True)
        await database.reports.create_index([("OwnerId", 1), ("ReportGeneratedAt", -1)])
        await database.reports.create_index([("OwnerId", 1), ("ReadingId", 1)], unique=True)
        # Create compound index on OwnerId and TrueTimestamp for hemoglobin_readings collection
        await database.hemoglobin_readings.create_index([("OwnerId", 1), ("TrueTimestamp", -1)])
        await database.hemoglobin_readings.create_index([("PatientId", 1), ("TrueTimestamp", -1)])
        # Create indexes for patients collection
        await database.patients.create_index("OwnerId")
        await database.patients.create_index([("OwnerId", 1), ("CreatedAt", -1)])
        await database.patients.create_index([("OwnerId", 1), ("Email", 1)], unique=True)
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
