import asyncio
import os
from bot import LOGGER, TG_SPLIT_SIZE
from bot.core.get_vars import get_val
from pyrogram import filters
from subprocess import run
from bot.downloaders.telegram.telegram_downloader import TelegramDownloader
from bot.uploaders.rclone.rclone_mirror import RcloneMirror
from bot.utils.misc_utils import clean_filepath
from bot.utils.zip_utils import extract_archive

async def handle_mirror_menu_callback(client, query):
        list = query.data.split("_")
        message= query.message
        tag = f"@{message.reply_to_message.from_user.username}"
        
        file= get_val("FILE")
        isZip = get_val("IS_ZIP")
        extract = get_val("EXTRACT")
        pswd = get_val("PSWD") 

        if "default" in list[1]:
            await mirror_file(client, message, file, tag, pswd, isZip=isZip, extract=extract)

        if "rename" in list[1]: 
            question= await client.send_message(message.chat.id, text= "Send the new name /ignore to cancel")
            try:
                response = await client.listen.Message(filters.text, id= tag, timeout = 30)
            except asyncio.TimeoutError:
                await question.reply("Cannot wait more longer for your response!")
            else:
                if response:
                    if "/ignore" in response.text:
                        await question.reply("Okay cancelled question!")
                        await client.listen.Cancel(tag)
                    else:
                        await mirror_file(client, message, file, tag, pswd, isZip=isZip, extract=extract, new_name=response.text, is_rename=True)
            finally:
                await question.delete()

async def mirror_file(client, message, file, tag, pswd, isZip, extract, new_name="", is_rename=False):
        mess_age= await message.reply_text('Starting download...', quote=True)
        DOWNLOAD_DIR = os.path.join(os.getcwd(), "Downloads", "")
        media_path= await TelegramDownloader(file, client, mess_age, DOWNLOAD_DIR).download() 
        if media_path is None:
            return
        if isZip:
            try:
                m_path = media_path
                await mess_age.edit("Zipping file...")
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
            await RcloneMirror(path, mess_age, tag, new_name, is_rename).mirror()        
            clean_filepath(m_path)
        elif extract:
            m_path = media_path
            await mess_age.edit("Extracting file...")
            extracted_path= await extract_archive(m_path, pswd)
            if extracted_path is not False:
                await RcloneMirror(extracted_path, mess_age, tag, new_name, is_rename).mirror()             
            else:
                await mess_age.edit('Unable to extract archive!')
            clean_filepath(m_path)
        else:
            await RcloneMirror(media_path, mess_age, tag, new_name, is_rename).mirror()