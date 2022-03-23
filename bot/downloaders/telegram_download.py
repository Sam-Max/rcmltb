import logging
import os
import time
from bot.core.get_vars import get_val
from bot.uploaders.rclone.rclone_mirror import rclone_uploader
from bot.utils.get_rclone_conf import get_config
from bot.downloaders.progress_for_pyrogram import progress_for_pyrogram

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
LOGGER = logging.getLogger(__name__)


async def down_load_media_pyro(client, message, media, tag, new_name= None, is_rename= False):
        mess_age = await message.reply_text("Preparing for download...", quote=True)
        
        LOGGER.info("downloading...")
        conf_path = await get_config()
        
        if conf_path is None:
            await mess_age.edit("Rclone config file not found.")
            return
        dest_drive = get_val("DEF_RCLONE_DRIVE")
        
        if dest_drive == "":
            await mess_age.edit("Select a cloud first please")
            return      
        
        path = os.path.join(os.getcwd(), "Downloads")
        path = path + "/"
        c_time = time.time()
        
        download_location = await client.download_media(
            message=media,
            file_name=path,
            progress=progress_for_pyrogram,
            progress_args=(
               "Name: `{}`".format(media.file_name),
               "Downloading...",
                mess_age, 
                c_time
            )
        )

        await rclone_uploader(download_location, mess_age, new_name, tag, is_rename)
        







