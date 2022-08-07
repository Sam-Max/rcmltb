
from bot import status_dict
from bot.downloaders.aria.aria_download import AriaDownloader
from bot.downloaders.mega.mega_download import MegaDownloader


async def handle_cancel(e):
   data = e.data.decode("UTF-8").split("_")
   if data[1] == "aria2":
        hashid = data[2]
        hashid = hashid.strip()
        ar_down= AriaDownloader(None, None)
        await ar_down.remove_dl(hashid)
   if data[1] == "megadl":  
        hashid = data[2]
        hashid = hashid.strip()
        mg_down = MegaDownloader(None, None)
        await mg_down.remove_mega_dl(hashid)
   if data[1] == "qbitdl":
        ext_hash = data[2]
        ext_hash = ext_hash.strip()
        for dl in list(status_dict.values()):
           if dl.ext_hash == ext_hash:
                dl.cancel_download()
                break  
   if data[1] == "rclone":
        ext_hash= data[2]
        ext_hash = int(ext_hash.strip())
        for dl in list(status_dict.values()):
            if dl.id == ext_hash:
                dl.cancelled = True
                break 
   if data[1] == "telegram":
     ext_hash = data[2]
     ext_hash = int(ext_hash.strip())
     for dl in list(status_dict.values()):
          if dl.id == ext_hash:
               dl.cancelled = True
               break 
        
 