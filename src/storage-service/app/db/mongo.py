import os
from motor.motor_asyncio import AsyncIOMotorClient
from app.utils.logger import DefaultLogger

logger = DefaultLogger("StorageService").get_logger()

MONGO_CONNECTION_STRING = os.getenv(
    "MONGO_CONNECTION_STRING", "mongodb://localhost:27017/factually_db"
)

class MongoClientSingleton:
    _client: AsyncIOMotorClient = None
    _db = None

    @classmethod
    async def init_client(cls):
        if cls._client is None:
            cls._client = AsyncIOMotorClient(MONGO_CONNECTION_STRING)
            cls._db = cls._client.get_default_database()
            logger.info("Connected to MongoDB")
        return cls._db

    @classmethod
    def get_db(cls):
        if cls._db is None:
            raise Exception("MongoDB client not initialized")
        return cls._db

    @classmethod
    async def close_client(cls):
        if cls._client is not None:
            cls._client.close()
            logger.info("MongoDB client closed")
            cls._client = None
            cls._db = None
        else:
            raise Exception("MongoDB client not initialized")