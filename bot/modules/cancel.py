
from pyrogram.filters import regex
from pyrogram.handlers import CallbackQueryHandler
from bot import Bot
from bot.helper.ext_utils.misc_utils import getDownloadByGid, getDownloadById

async def handle_cancel(client, callback_query):
   data = callback_query.data.split("_")
   if data[1] == "aria2":
        gid = data[2]
        gid = gid.strip()
        dl = await getDownloadByGid(gid)
        dl.cancel_download()
   if data[1] == "megadl":  
        gid = data[2]
        gid = gid.strip()
        dl = await getDownloadByGid(gid)
        await dl.cancel_download() 
   if data[1] == "qbitdl":
        gid = data[2]
        gid = gid.strip()
        dl = await getDownloadByGid(gid)
        dl.cancel_download() 
   if data[1] == "rclone":
        id= data[2]
        id = int(id.strip())
        dl = await getDownloadById(id)
        dl.is_cancelled = True
   if data[1] == "telegram":
        id = data[2]
        id = int(id.strip())
        dl = await getDownloadById(id)
        dl.is_cancelled = True

cancel= CallbackQueryHandler(handle_cancel, filters= regex("cancel"))
Bot.add_handler(cancel)        
        
 