import motor.motor_asyncio
from os import environ

# 🔹 MongoDB Connection
DATABASE_URI = environ.get('DATABASE_URI', "")
DATABASE_NAME = environ.get('DATABASE_NAME', "TELEGRAM_BOT_INFO")
COLLECTION_NAME = environ.get('COLLECTION_NAME', 'tele_data')

client = motor.motor_asyncio.AsyncIOMotorClient(DATABASE_URI)
db = client[DATABASE_NAME] if client is not None else None

class UserDownload:
    collection = db[COLLECTION_NAME] if db is not None else None

    def __init__(self, _id, file_count=0):
        self._id = _id
        self.file_count = file_count

    @staticmethod
    async def insert_one(data):
        if UserDownload.collection is not None:
            return await UserDownload.collection.insert_one(data)
        return None

    @staticmethod
    async def find_one(query):
        if UserDownload.collection is not None:
            return await UserDownload.collection.find_one(query)
        return None

    @staticmethod
    async def update_one(query, new_data):
        if UserDownload.collection is not None:
            return await UserDownload.collection.update_one(query, {"$set": new_data})
        return None

    @staticmethod
    async def delete_one(query):
        if UserDownload.collection is not None:
            return await UserDownload.collection.delete_one(query)
        return None
