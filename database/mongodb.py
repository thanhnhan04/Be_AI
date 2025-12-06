from motor.motor_asyncio import AsyncIOMotorClient
from config import settings


class MongoDB:
    """MongoDB connection manager"""
    
    client: AsyncIOMotorClient = None
    database = None


mongodb = MongoDB()


async def connect_to_mongodb():
    """Connect to MongoDB database"""
    try:
        mongodb.client = AsyncIOMotorClient(settings.MONGODB_URL)
        mongodb.database = mongodb.client[settings.MONGODB_DB_NAME]
        
        # Test connection
        await mongodb.client.admin.command('ping')
        print(f"✓ Connected to MongoDB: {settings.MONGODB_DB_NAME}")
    except Exception as e:
        print(f"✗ Could not connect to MongoDB: {e}")
        raise


async def close_mongodb_connection():
    """Close MongoDB connection"""
    if mongodb.client:
        mongodb.client.close()
        print("✓ Closed MongoDB connection")


def get_database():
    """Get database instance"""
    return mongodb.database


# Collection names
USERS_COLLECTION = "users"  # Recommendation users (from sync or Yelp data)
EXPERIENCES_COLLECTION = "experiences"
INTERACTIONS_COLLECTION = "interactions"
USER_SIMILARITY_COLLECTION = "user_similarities"
