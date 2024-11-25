#By @Silicon_Bot_Update 
#Distribute and edit it as your wish but please don't remove credit 😓😓
#By stealing Credit of Developer you will not become pro so try to give full credit to Developer 🥺🥺🥺

import os
import requests
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def upload_image_requests(image_path):
    upload_url = "https://envs.sh"

    try:
        with open(image_path, 'rb') as file:
            files = {'file': file} 
            response = requests.post(upload_url, files=files)

            if response.status_code == 200:
                return response.text.strip() 
            else:
                raise Exception(f"Upload failed with status code {response.status_code}")

    except Exception as e:
        print(f"Error during upload: {e}")
        return None

#By @Silicon_Bot_Update 
#Distribute and edit it as your wish but please don't remove credit 😓😓
#By stealing Credit of Developer you will not become pro so try to give full credit to Developer 🥺🥺🥺

@Client.on_message(filters.command("telegraph") & filters.private)
async def upload_command(client, message):
    replied = message.reply_to_message
    if not replied:
        await message.reply_text("Reply to a photo or video under 512 MB.")
        return

    if replied.media and hasattr(replied, 'file_size'):
        if replied.file_size > 536870912:
            await message.reply_text("File size is greater than 512 MB.")
            return

    silicon_path = await replied.download()

    uploading_message = await message.reply_text("<code>Uploading...</code>")

    try:
        silicon_url = upload_image_requests(silicon_path)
        if not silicon_url:
            raise Exception("Failed to upload file.")
    except Exception as error:
        await uploading_message.edit_text(f"Upload failed: {error}")
        return

    try:
        os.remove(silicon_path)
    except Exception as error:
        print(f"Error removing file: {error}")

    await uploading_message.edit_text(
        text=f"<b>Link :-</b>\n\n<code>{silicon_url}</code>",
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(text="Open Link", url=silicon_url),
            InlineKeyboardButton(text="Share Link", url=f"https://telegram.me/share/url?url={silicon_url}")
        ], [
            InlineKeyboardButton(text="Close this menu", callback_data="close_data")
        ]])
    )

#By @Silicon_Bot_Update 
#Distribute and edit it as your wish but please don't remove credit 😓😓
#By stealing Credit of Developer you will not become pro so try to give full credit to Developer 🥺🥺🥺
