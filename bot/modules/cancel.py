
from bot import bot
from telethon.events import CallbackQuery
from bot.helper.ext_utils.misc_utils import getDownloadByGid, getDownloadById

async def handle_cancel(e):
   data = e.data.decode("UTF-8").split("_")
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
        await dl.cancel_download("Download stopped by user!!") 
   if data[1] == "rclone":
        id= data[2]
        id = int(id.strip())
        dl = await getDownloadById(id)
        dl.cancelled = True
   if data[1] == "telegram":
        id = data[2]
        id = int(id.strip())
        dl = await getDownloadById(id)
        dl.cancelled = True

bot.add_event_handler(
        handle_cancel,
        CallbackQuery(pattern="cancel"))
        
 