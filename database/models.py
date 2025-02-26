import motor.motor_asyncio
from os import environ

# MongoDB Connection
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

    async def save(self):
        """नए यूजर को डेटाबेस में सेव करने के लिए"""
        if UserDownload.collection is not None:
            return await UserDownload.collection.insert_one(self.__dict__)
        return None

    @staticmethod
    async def find_one(query):
        """यूजर को डेटाबेस में सर्च करने के लिए"""
        if UserDownload.collection is not None:
            return await UserDownload.collection.find_one(query)
        return None

    @staticmethod
    async def insert_one(data):
        """नए डेटा को डेटाबेस में डालने के लिए"""
        if UserDownload.collection is not None:
            return await UserDownload.collection.insert_one(data)
        return None

    @staticmethod
    async def update_one(query, new_data):
        """यूजर का डेटा अपडेट करने के लिए (TypeError फिक्स किया गया)"""
        if UserDownload.collection is not None:
            return await UserDownload.collection.update_one(query, {"$set": new_data})
        return None

    @staticmethod
    async def delete_one(query):
        """यूजर को डेटाबेस से हटाने के लिए"""
        if UserDownload.collection is not None:
            return await UserDownload.collection.delete_one(query)
        return None
