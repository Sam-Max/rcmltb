import asyncio
import os
from bot import DOWNLOAD_DIR, LOGGER, TG_SPLIT_SIZE
from bot.core.get_vars import get_val
from pyrogram import filters
from subprocess import run
from bot.downloaders.telegram.telegram_downloader import TelegramDownloader
from bot.uploaders.rclone.rclone_mirror import RcloneMirror
from bot.utils.bot_utils.misc_utils import clean
from bot.utils.bot_utils.zip_utils import extract_archive

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
        mess_age= await message.reply_text('Starting download...')
        await message.delete()
        tg_down= TelegramDownloader(file, client, mess_age, DOWNLOAD_DIR)
        media_path= await tg_down.download() 
        if media_path is None:
            return
        m_path = media_path
        if isZip:
            try:
                base = os.path.basename(m_path)
                file_name = base.rsplit('.', maxsplit=1)[0]
                file_name = file_name + ".zip"
                path = f'{DOWNLOAD_DIR}{file_name}'
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
        elif extract:
            path, msg= await extract_archive(m_path, pswd)
            if path == False:
                return await mess_age.edit(msg)
        else:
            path= m_path
        rc_mirror= RcloneMirror(path, mess_age, tag, new_name, is_rename= is_rename)
        await rc_mirror.mirror()   