from aiohttp import web

routes = web.RouteTableDef()

@routes.get("/", allow_head=True)
async def root_route_handler(request):
    return web.json_response("Elsa")

from pyrogram import Client, filters

# ग्रुप में मैसेज ब्लॉक करने के लिए
@Client.on_message(filters.group & filters.text)
def block_in_groups(client, message):
    message.reply_text("माफ करें, यह बॉट केवल प्राइवेट चैट (PM) में काम करता है।")
