import os
import time
from subprocess import run
from bot import GLOBAL_RC_INST
from bot.core.get_vars import get_val
from bot.uploaders.rclone.rclone_mirror import RcloneMirror
from bot.utils.get_rclone_conf import get_config
from bot.downloaders.progress_for_pyrogram import progress_for_pyrogram
from bot import LOGGER
from bot.utils.misc_utils import clean_filepath
from bot.utils.zip_utils import extract_archive

async def down_load_media_pyro(client, message, media, tag, pswd, isZip=False, extract=False, new_name=None, is_rename= False):
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
        c_time))
    if isZip:
        m_path = media_path
        LOGGER.info("Compressing...")
        await mess_age.edit("Compressing...")
        base = os.path.basename(m_path)
        file_name = base.rsplit('.', maxsplit=1)[0]
        path = os.path.join(os.getcwd(), "Downloads", file_name + ".zip")
        LOGGER.info(f'Zip: orig_path: {m_path}, zip_path: {path}')
        size = os.path.getsize(m_path)
        TG_SPLIT_SIZE= get_val("TG_SPLIT_SIZE")
        if pswd is not None:
            LOGGER.info("Password: {}".format(pswd))     
            if int(size) > TG_SPLIT_SIZE:
                run(["7z", f"-v{TG_SPLIT_SIZE}b", "a", "-mx=0", f"-p{pswd}", path, m_path])     
            else:
                run(["7z", "a", "-mx=0", f"-p{pswd}", path, m_path])
        elif int(size) > TG_SPLIT_SIZE:
            run(["7z", f"-v{TG_SPLIT_SIZE}b", "a", "-mx=0", path, m_path])
        else:
            run(["7z", "a", "-mx=0", path, m_path])
        clean_filepath(m_path)
        await rclone_mirror(path, mess_age, new_name, tag, is_rename)
    elif extract:
        m_path = media_path
        LOGGER.info("Extracting...")
        await mess_age.edit("Extracting...")
        extracted_path= await extract_archive(m_path, pswd)
        clean_filepath(m_path)
        if extracted_path is not False:
            await rclone_mirror(extracted_path, mess_age, new_name, tag, is_rename)
        else:
            LOGGER.error('Unable to extract archive!')
    else:
        await rclone_mirror(media_path, mess_age, new_name, tag, is_rename)

async def rclone_mirror(path, mess_age, new_name, tag, is_rename):
    rclone_mirror= RcloneMirror(path, mess_age, new_name, tag, is_rename)
    GLOBAL_RC_INST.append(rclone_mirror)
    await rclone_mirror.mirror()
    GLOBAL_RC_INST.remove(rclone_mirror)

class NotSupportedExtractionArchive(Exception):
    """The archive format use is trying to extract is not supported"""
    pass
