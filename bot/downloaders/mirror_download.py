import os
from subprocess import run
from bot import LOGGER, MEGA_KEY, TG_SPLIT_SIZE
from bot.core.get_vars import get_val
from bot.downloaders.aria.aria_download import AriaDownloader
from bot.downloaders.mega.mega_download import MegaDownloader
from bot.downloaders.qbit.qbit_downloader import QbDownloader
from bot.downloaders.telegram.telegram_downloader import TelegramDownloader
from bot.uploaders.rclone.rclone_mirror import RcloneMirror
from bot.utils.bot_utils import is_mega_link
from bot.utils.get_rclone_conf import get_config
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

    conf_path = await get_config()
    if conf_path is None:
        return await message.reply_text("Rclone config file not found.")
        
    if len(get_val("DEF_RCLONE_DRIVE")) == 0:
        return await message.reply_text("You need to select a cloud first, use /mirrorset")
    
    mess_age = await message.reply_text("Preparing for download...", quote=True)
          
    if file is None:
        if is_mega_link(link):
            if MEGA_KEY is not None:
                mega_dl= MegaDownloader(link, mess_age)   
                state, message, path= await mega_dl.execute()
                if not state:
                    await mess_age.edit(message)
                    clean_path(path)
                else:
                    await RcloneMirror(path, mess_age, new_name, tag, is_rename).mirror()
            else:
                 await mess_age.edit("MEGA_API_KEY not provided!")
        elif isQbit:
             qbit_dl= QbDownloader(mess_age)
             state, message, path= await qbit_dl.add_qb_torrent(link)
             if not state:
                await mess_age.edit(message)
                clean_path(path)
             else:
                await RcloneMirror(path, mess_age, new_name, tag, is_rename).mirror()
        else:
            aria2= AriaDownloader(link, mess_age)   
            state, message, path= await aria2.execute()
            if not state:
                await mess_age.edit(message)
            else:
                await RcloneMirror(path, mess_age, new_name, tag, is_rename).mirror()     
    else:
        DOWNLOAD_DIR = os.path.join(os.getcwd(), "Downloads", "")
        media_path= await TelegramDownloader(file, client, mess_age, DOWNLOAD_DIR).download() 
        if media_path is None:
            return
        if isZip:
            try:
                m_path = media_path
                await mess_age.edit("Compressing...")
                base = os.path.basename(m_path)
                file_name = base.rsplit('.', maxsplit=1)[0]
                path = os.path.join(os.getcwd(), "Downloads", file_name + ".zip")
                LOGGER.info(f'Zip: orig_path: {m_path}, zip_path: {path}')
                size = os.path.getsize(m_path)
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
            await RcloneMirror(path, mess_age, new_name, tag, is_rename).mirror()        
            clean_filepath(m_path)
        elif extract:
            m_path = media_path
            await mess_age.edit("Extracting...")
            extracted_path= await extract_archive(m_path, pswd)
            if extracted_path is not False:
                await RcloneMirror(extracted_path, mess_age, new_name, tag, is_rename).mirror()             
            else:
                await mess_age.edit('Unable to extract archive!')
            clean_filepath(m_path)
        else:
            await RcloneMirror(media_path, mess_age, new_name, tag, is_rename).mirror()

