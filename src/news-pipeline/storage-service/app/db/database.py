import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_CONNECTION_STRING = os.getenv("MONGO_CONNECTION_STRING", "mongodb://localhost:27017/factually_db")
client = AsyncIOMotorClient(MONGO_CONNECTION_STRING)
db = client.get_default_database()