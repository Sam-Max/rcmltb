import os
import time
from subprocess import run
from bot import GLOBAL_RC_INST
from bot.core.get_vars import get_val
from bot.uploaders.rclone.rclone_mirror import RcloneMirror
from bot.utils.get_rclone_conf import get_config
from bot.downloaders.progress_for_pyrogram import progress_for_pyrogram
from bot import LOGGER


async def down_load_media_pyro(client, message, media, tag, isZip=False, new_name=None, is_rename= False):
    mess_age = await message.reply_text("Preparing for download...", quote=True)
    LOGGER.info("Downloading...")
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
    
    media_path = await client.download_media(
        message=media,
        file_name=path,
        progress=progress_for_pyrogram,
        progress_args=(
        "**Name**: `{}`".format(media.file_name),
        "**Status:** Downloading...",
            mess_age, 
            c_time
        )
    )
    
    if isZip:
        try:
            m_path = media_path
            path = m_path + ".zip"
            LOGGER.info(f'Zip: orig_path: {m_path}, zip_path: {path}')
            size = os.path.getsize(m_path)
            TG_SPLIT_SIZE= get_val("TG_SPLIT_SIZE")
            if int(size) > TG_SPLIT_SIZE:
                run(["7z", f"-v{TG_SPLIT_SIZE}b", "a", "-mx=0", path, m_path])
            else:
                run(["7z", "a", "-mx=0", path, m_path])
            rclone_mirror= RcloneMirror(path, mess_age, new_name, tag, is_rename)
            GLOBAL_RC_INST.append(rclone_mirror)
            await rclone_mirror.mirror()
            GLOBAL_RC_INST.remove(rclone_mirror)
        except FileNotFoundError:
            LOGGER.info('File to archive not found!')
            return
    else:
        rclone_mirror= RcloneMirror(media_path, mess_age, new_name, tag, is_rename)
        GLOBAL_RC_INST.append(rclone_mirror)
        await rclone_mirror.mirror()
        GLOBAL_RC_INST.remove(rclone_mirror)