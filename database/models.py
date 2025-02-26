from pymongo import MongoClient
from info import DATABASE_URI, DATABASE_NAME, COLLECTION_NAME  # ⬅ info.py से Import किया
from motor.motor_asyncio import AsyncIOMotorClient  # ✅ Motor for Async MongoDB

try:
    client = AsyncIOMotorClient(DATABASE_URI)
    db = client[DATABASE_NAME]
    print("✅ MongoDB Connection Successful!")  # Check if connection is established
except Exception as e:
    print(f"❌ MongoDB Connection Failed: {e}")
    db = None

# ✅ UserDownload Model बनाएं
class UserDownload:
    collection = db[COLLECTION_NAME] if db else None  # 🛑 Handle None Case

    @staticmethod
    async def find_one(query):
        if UserDownload.collection is None:
            print("❌ Error: Collection is None!")
            return None
        return await UserDownload.collection.find_one(query)
    

# ✅ MongoDB से कनेक्ट करें
client = MongoClient(DATABASE_URI)
db = client[DATABASE_NAME]  # Database से कनेक्ट करें

# ✅ UserDownload Model बनाएं
class UserDownload:
    collection = db[COLLECTION_NAME]  # Collection सेट करें

    @staticmethod
    async def find_one(query):
        """ यूज़र की जानकारी ढूंढने के लिए """
        return await UserDownload.collection.find_one(query)

    @staticmethod
    async def insert_one(data):
        """ नया यूज़र जोड़ने के लिए """
        return await UserDownload.collection.insert_one(data)

    @staticmethod
    async def update_one(query, update_data):
        """ यूज़र की जानकारी अपडेट करने के लिए """
        return await UserDownload.collection.update_one(query, {"$set": update_data})

    @staticmethod
    async def delete_one(query):
        """ यूज़र की जानकारी डिलीट करने के लिए """
        return await UserDownload.collection.delete_one(query)

    @staticmethod
    async def count_documents(query={}):
        """ यूज़र्स की संख्या गिनने के लिए """
        return await UserDownload.collection.count_documents(query)
