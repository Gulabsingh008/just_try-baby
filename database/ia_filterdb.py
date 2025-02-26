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
from database.models import UserDownload

async def check_download_limit(user_id):
    """यूजर का डाउनलोड लिमिट चेक और अपडेट करने के लिए फंक्शन"""
    
    query = {"_id": user_id}  # ✅ यूजर की MongoDB में पहचान
    user = await UserDownload.find_one(query)

    max_limit = 10  # ✅ मैक्सिमम डाउनलोड लिमिट (इसे अपनी जरूरत के अनुसार बदल सकते हैं)

    if user:
        file_count = user.get("file_count", 0)

        if file_count >= max_limit:
            return False, max_limit  # ❌ लिमिट पूरी हो गई, डाउनलोड ब्लॉक

        # ✅ सही तरीके से update_one() को कॉल किया
        new_data = {"file_count": file_count + 1}
        await UserDownload.update_one(query, new_data)  # ✅ Static Method को Class से कॉल किया

        return True, max_limit

    else:
        # ✅ नया यूजर, डेटा सेव करें
        new_user = {"_id": user_id, "file_count": 1}
        await UserDownload.insert_one(new_user)
        return True, max_limit

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
    upload_date = fields.DateTimeField(allow_none=True)  # New Feature: Upload Date

    class Meta:
        indexes = ('$file_name', )
        collection_name = COLLECTION_NAME

async def get_files_db_size():
    return (await mydb.command("dbstats"))['dataSize']
    
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
            file_type=media.mime_type.split('/')[0],
            upload_date=media.date  # Storing upload date
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

async def get_search_results(query, max_results=MAX_BTN, offset=0, lang=None):
    query = query.strip()
    if not query:
        raw_pattern = '.'
    elif ' ' not in query:
        raw_pattern = r'(\b|[\.\+\-_])' + query + r'(\b|[\.\+\-_])'
    else:
        raw_pattern = query.replace(' ', r'.*[\s\.\+\-_]') 
    try:
        regex = re.compile(raw_pattern, flags=re.IGNORECASE)
    except:
        regex = query
    filter = {'file_name': regex}
    cursor = Media.find(filter)
    cursor.sort('$natural', -1)
    if lang:
        lang_files = [file async for file in cursor if lang in file.file_name.lower()]
        files = lang_files[offset:][:max_results]
        total_results = len(lang_files)
        next_offset = offset + max_results
        if next_offset >= total_results:
            next_offset = ''
        return files, next_offset, total_results
    cursor.skip(offset).limit(max_results)
    files = await cursor.to_list(length=max_results)
    total_results = await Media.count_documents(filter)
    next_offset = offset + max_results
    if next_offset >= total_results:
        next_offset = ''       
    return files, next_offset, total_results
    
async def get_bad_files(query, file_type=None, offset=0, filter=False):
    query = query.strip()
    if not query:
        raw_pattern = '.'
    elif ' ' not in query:
        raw_pattern = r'(\b|[\.\+\-_])' + query + r'(\b|[\.\+\-_])'
    else:
        raw_pattern = query.replace(' ', r'.*[\s\.\+\-_]')
    try:
        regex = re.compile(raw_pattern, flags=re.IGNORECASE)
    except:
        return []
    filter = {'file_name': regex}
    if file_type:
        filter['file_type'] = file_type
    total_results = await Media.count_documents(filter)
    cursor = Media.find(filter)
    cursor.sort('$natural', -1)
    files = await cursor.to_list(length=total_results)
    return files, total_results
    
async def get_file_details(query):
    filter = {'file_id': query}
    cursor = Media.find(filter)
    filedetails = await cursor.to_list(length=1)
    return filedetails

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
        await user.update_one()
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
