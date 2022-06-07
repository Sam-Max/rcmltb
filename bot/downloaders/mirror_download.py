import os
import time
from subprocess import run
from bot import GLOBAL_RCLONE, MEGA_KEY
from bot.core.get_vars import get_val
from bot.downloaders.aria.aria_download import AriaDownloader
from bot.downloaders.mega.mega_download import MegaDownloader
from bot.downloaders.qbit.qbit_downloader import QbDownloader
from bot.uploaders.rclone.rclone_mirror import RcloneMirror
from bot.utils.bot_utils import is_mega_link
from bot.utils.get_rclone_conf import get_config
from bot.downloaders.progress_for_pyrogram import progress_for_pyrogram
from bot import LOGGER
from bot.utils.misc_utils import clean_filepath, clean_path
from bot.utils.zip_utils import extract_archive

async def handle_mirror_download(
    client, 
    message, 
    file, 
    tag, 
    pswd, 
    link="", 
    isZip=False, 
    extract=False, 
    isQbit=False, 
    new_name="", 
    is_rename= False
    ):
    mess_age = await message.reply_text("Preparing for download...", quote=True)
    LOGGER.info("Preparing for download...")

    conf_path = await get_config()
    if conf_path is None:
        await mess_age.edit("Rclone config file not found.")
        return

    if get_val("DEF_RCLONE_DRIVE") == "":
        await mess_age.edit("Select a cloud first please")
        return      

    if file is None:
        if is_mega_link(link):
            if MEGA_KEY is not None:
                mega_dl= MegaDownloader(link, mess_age)   
                state, message, path= await mega_dl.execute()
                if not state:
                    await mess_age.edit(message)
                    clean_path(path)
                else:
                    await rclone_mirror(path, mess_age, new_name, tag, is_rename) 
            else:
                await rclone_mirror(path, mess_age, new_name, tag, is_rename) 
        elif isQbit:
             qbit_dl= QbDownloader(mess_age)
             state, message, path= await qbit_dl.add_qb_torrent(link)
             if not state:
                await mess_age.edit(message)
                clean_path(path)
             else:
                await rclone_mirror(path, mess_age, new_name, tag, is_rename) 
        else:
            aria2= AriaDownloader(link, mess_age)   
            state, message, path= await aria2.execute()
            if not state:
                await mess_age.edit(message)
            else:
                await rclone_mirror(path, mess_age, new_name, tag, is_rename) 
    else:
        c_time = time.time()
        DOWNLOAD_DIR = os.path.join(os.getcwd(), "Downloads", "")
        media_path = await client.download_media(
            message=file,
            file_name= DOWNLOAD_DIR,
            progress=progress_for_pyrogram,
            progress_args=(
            "**Name**: `{}`".format(file.file_name),
            "**Status:** Downloading...",
            mess_age, 
            c_time))
            
        if isZip:
            try:
                m_path = media_path
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
            except FileNotFoundError:
                LOGGER.info('File to archive not found!')
                return
            await rclone_mirror(path, mess_age, new_name, tag, is_rename)
            clean_filepath(m_path)
        elif extract:
            m_path = media_path
            await mess_age.edit("Extracting...")
            extracted_path= await extract_archive(m_path, pswd)
            if extracted_path is not False:
                await rclone_mirror(extracted_path, mess_age, new_name, tag, is_rename)
            else:
                await mess_age.edit('Unable to extract archive!')
            clean_filepath(m_path)
        else:
            await rclone_mirror(media_path, mess_age, new_name, tag, is_rename)

async def rclone_mirror(path, mess_age, new_name, tag, is_rename):
    rclone_mirror= RcloneMirror(path, mess_age, new_name, tag, is_rename)
    GLOBAL_RCLONE.append(rclone_mirror)
    await rclone_mirror.mirror()
    GLOBAL_RCLONE.remove(rclone_mirror)

