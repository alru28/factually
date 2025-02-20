import os
from motor.motor_asyncio import AsyncIOMotorClient

"""
This module sets up the connection to the MongoDB database using Motor (the async MongoDB driver).
It exports a 'db' object which is used by the storage service to interact with the database.
"""

MONGO_CONNECTION_STRING = os.getenv("MONGO_CONNECTION_STRING", "mongodb://localhost:27017/factually_db")
client = AsyncIOMotorClient(MONGO_CONNECTION_STRING)
db = client.get_default_database()