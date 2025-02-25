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

async def save_file(media):
    """Save file in database"""

    file_id, file_ref = unpack_new_file_id(media.file_id)
    file_name = re.sub(r"(_|\-|\.|\+)", " ", str(media.file_name))
    try:
        file = Media(
            file_id=file_id,
            file_ref=file_ref,
            file_name=file_name,
            file_size=media.file_size,
            mime_type=media.mime_type,
            caption=media.caption.html if media.caption else None,
            file_type=media.mime_type.split('/')[0]
        )
    except ValidationError:
        print('Error occurred while saving file in database')
        return 'err'
    else:
        try:
            await file.commit()
        except DuplicateKeyError:      
            print(f'{getattr(media, "file_name", "NO_FILE")} is already saved in database') 
            return 'dup'
        else:
            print(f'{getattr(media, "file_name", "NO_FILE")} is saved to database')
            return 'suc'


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

def encode_file_id(s: bytes) -> str:
    r = b""
    n = 0
    for i in s + bytes([22]) + bytes([4]):
        if i == 0:
            n += 1
        else:
            if n:
                r += b"\x00" + bytes([n])
                n = 0
            r += bytes([i])
    return base64.urlsafe_b64encode(r).decode().rstrip("=")

def encode_file_ref(file_ref: bytes) -> str:
    return base64.urlsafe_b64encode(file_ref).decode().rstrip("=")

def unpack_new_file_id(new_file_id):
    """Return file_id, file_ref"""
    decoded = FileId.decode(new_file_id)
    file_id = encode_file_id(
        pack(
            "<iiqq",
            int(decoded.file_type),
            decoded.dc_id,
            decoded.media_id,
            decoded.access_hash
        )
    )
    file_ref = encode_file_ref(decoded.file_reference)
    return file_id, file_ref
