
from bot import GLOBAL_RC_INST, LOGGER
from bot.downloaders.aria.aria_download import AriaDownloader


async def handle_cancel(e):
   data = e.data.decode("UTF-8").split("_")
   if data[1] == "aria2":
        hashid = data[2]
        hashid = hashid.strip("'")
        LOGGER.info(f"Hashid :- {hashid}")
        await AriaDownloader(None, None).remove_dl(hashid)
   if data[1] == "rclone":
        id= data[2]
        for rc_up in GLOBAL_RC_INST:
            if rc_up.id == id:
                rc_up.cancel = True
                break  