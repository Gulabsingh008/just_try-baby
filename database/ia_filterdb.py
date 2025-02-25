import logging
from struct import pack
import re
import base64
from pyrogram.file_id import FileId
from pymongo.errors import DuplicateKeyError
from umongo import Instance, Document, fields
from motor.motor_asyncio import AsyncIOMotorClient
from marshmallow.exceptions import ValidationError
from info import DATABASE_URI, DATABASE_NAME, COLLECTION_NAME, MAX_BTN, PREMIUM_USERS
from datetime import datetime, timedelta

client = AsyncIOMotorClient(DATABASE_URI)
mydb = client[DATABASE_NAME]
instance = Instance.from_db(mydb)

@instance.register
class Media(Document):
    file_id = fields.StrField(attribute='_id')
    file_ref = fields.StrField(allow_none=True)
    file_name = fields.StrField(required=True)
    file_size = fields.IntField(required=True)
    mime_type = fields.StrField(allow_none=True)
    caption = fields.StrField(allow_none=True)
    file_type = fields.StrField(allow_none=True)

    class Meta:
        indexes = ('$file_name', )
        collection_name = COLLECTION_NAME

@instance.register
class UserDownload(Document):
    user_id = fields.IntField(attribute='_id')
    file_count = fields.IntField(default=0)
    last_reset = fields.DateTimeField(default=datetime.utcnow)
    
    class Meta:
        collection_name = "user_downloads"

async def get_files_db_size():
    return (await mydb.command("dbstats"))['dataSize']

async def check_download_limit(user_id):
    user = await UserDownload.find_one({'_id': user_id})
    is_premium = user_id in PREMIUM_USERS
    max_limit = 15 if is_premium else 3
    
    if user:
        if datetime.utcnow() - user.last_reset >= timedelta(days=1):
            user.file_count = 0
            user.last_reset = datetime.utcnow()
            await user.commit()
        if user.file_count >= max_limit:
            return False, max_limit  # Limit reached
    else:
        user = UserDownload(_id=user_id, file_count=0)
        await user.commit()
    return True, max_limit

async def increment_download_count(user_id):
    user = await UserDownload.find_one({'_id': user_id})
    if user:
        user.file_count += 1
        await user.commit()
    else:
        user = UserDownload(_id=user_id, file_count=1)
        await user.commit()

async def get_file_by_name(file_name):
    file_name = file_name.strip()
    filter = {'file_name': {'$regex': file_name, '$options': 'i'}}
    cursor = Media.find(filter)
    file = await cursor.to_list(length=1)
    return file[0] if file else None
