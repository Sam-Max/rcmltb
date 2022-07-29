
from bot import GLOBAL_QBIT, GLOBAL_RCLONE, GLOBAL_TG_DOWNLOADER, LOGGER
from bot.downloaders.aria.aria_download import AriaDownloader
from bot.downloaders.mega.mega_download import MegaDownloader


async def handle_cancel(e):
   data = e.data.decode("UTF-8").split("_")
   if data[1] == "aria2":
        hashid = data[2]
        hashid = hashid.strip("'")
        LOGGER.info(f"Hashid :- {hashid}")
        await AriaDownloader(None, None).remove_dl(hashid)
   if data[1] == "megadl":  
        hashid = data[2]
        hashid = hashid.strip("'")
        LOGGER.info(f"Hashid :- {hashid}")
        await MegaDownloader(None, None).remove_mega_dl(hashid)
   if data[1] == "qbitdl":
        ext_hash = data[2]
        ext_hash = ext_hash.strip("'")
        for dl in GLOBAL_QBIT:
           if dl.ext_hash == ext_hash:
                dl.cancel_download()
                break  
   if data[1] == "rclone":
        ext_hash= data[2]
        ext_hash = ext_hash.strip("'")
        for dl in GLOBAL_RCLONE:
            if dl.id == ext_hash:
                dl.cancelled = True
                break 
   if data[1] == "tgdown":
     ext_hash = data[2]
     ext_hash = ext_hash.strip("'")
     for dl in GLOBAL_TG_DOWNLOADER:
          if dl.id == ext_hash:
               dl.cancel_download()
               break 
        
 