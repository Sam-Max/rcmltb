
from bot import LOGGER, status_dict
from bot.utils.bot_utils.misc_utils import getDownloadByGid


async def handle_cancel(e):
   data = e.data.decode("UTF-8").split("_")
   if data[1] == "aria2":
        gid = data[2]
        gid = gid.strip()
        for dl in list(status_dict.values()):
          if dl.gid() == gid:
               dl.cancel_download()
               break  
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
        hashid= data[2]
        hashid = int(hashid.strip())
        for dl in list(status_dict.values()):
            if dl.id == hashid:
                dl.cancelled = True
                break 
   if data[1] == "telegram":
     hashid = data[2]
     hashid = int(hashid.strip())
     for dl in list(status_dict.values()):
          if dl.id == hashid:
               dl.cancelled = True
               break 
        
 