from pymongo import MongoClient

# MongoDB से कनेक्ट करें
client = MongoClient("your_mongodb_connection_string")
db = client["your_database_name"]

# UserDownload Model बनाएं
class UserDownload:
    collection = db["user_downloads"]

    @staticmethod
    async def find_one(query):
        return await UserDownload.collection.find_one(query)

    @staticmethod
    async def insert_one(data):
        return await UserDownload.collection.insert_one(data)
