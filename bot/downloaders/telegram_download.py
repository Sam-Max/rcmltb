# -*- coding: utf-8 -*-

# the logging things
import logging
from pyrogram import types
from bot import SessionVars
import asyncio
import os
import time
from datetime import datetime
from bot.core.getVars import get_val
from bot.utils.get_rclone_conf import get_config
from ..uploaders.rclone_upload import RcloneUploader
from telethon.tl import types
from bot.downloaders.progress_for_pyrogram import progress_for_pyrogram

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
LOGGER = logging.getLogger(__name__)


class Timer:
    def __init__(self, time_between=2):
        self.start_time = time.time()
        self.time_between = time_between

    def can_send(self):
        if time.time() > (self.start_time + self.time_between):
            self.start_time = time.time()
            return True
        return False


# TELETHON
async def download_media_tele(e):
    type_of = ""
    message = None
    timer = Timer()

    async def progress_bar(current, total):
        if timer.can_send():
            await message.edit("{} {}%".format(type_of, current * 100 / total))

    if e.message.media is not None:
        file_name = "unknown"
        attributes = e.message.media.document.attributes
        for attr in attributes:
            if isinstance(attr, types.DocumentAttributeFilename):
                file_name = attr.file_name
                LOGGER.info(file_name)
        file_path = os.path.join(os.getcwd(), "Downloads")
        file_path = file_path + "/"
        message = await e.reply('Downloading...')
        LOGGER.info("[%s] Download started at %s" % (file_name, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
        try:
            await e.client.download_media(e.message, file_path, progress_callback=progress_bar)
            print("Successfully downloaded")

            update_msg = await message.reply("Starting the rclone upload.")

            rclone_up = RcloneUploader(file_path, update_msg, SessionVars.get("DEF_RCLONE_DRIVE"))

            await rclone_up.execute()

        except asyncio.TimeoutError:
            await message.edit('Error!')
            message = await message.reply('ERROR: Timeout reached downloading this file')
        except Exception as e:
            await message.edit('Error!')
            message = await message.reply(
                'ERROR: Exception %s raised downloading this file: %s' % (e.__class__.__name__, str(e)))
    else:
        await e.reply('Send a media file')


# PYROGRAM
async def down_load_media_pyro(client, message, message_type, new_name= None, is_rename= False):
        mess_age = await message.reply_text("...", quote=True)
        LOGGER.info("downloading with pyro client")
        conf_path = await get_config()
        if conf_path is None:
            await mess_age.edit("No se encontró el archivo de configuración rclone.")
            return
        dest_drive = get_val("DEF_RCLONE_DRIVE")
        if dest_drive == "":
            await mess_age.edit("No ha seleccionado una unidad a donde subir")
            return      
        start_t = datetime.now()
        path = os.path.join(os.getcwd(), "Downloads")
        path = path + "/"
        c_time = time.time()
        the_real_download_location = await client.download_media(
            message=message_type,
            file_name=path,
            progress=progress_for_pyrogram,
            progress_args=(
               "Descargando...", mess_age, c_time
            )
        )
        end_t = datetime.now()
        ms = (end_t - start_t).seconds
        print(the_real_download_location)

        try:
            await mess_age.edit(text= f"Descargado en <u>{ms}</u> segundos")
        except Exception as e:
            LOGGER.info(e)
            pass
        
        rclone_up = RcloneUploader(the_real_download_location, mess_age, new_name, is_rename= is_rename)
        await rclone_up.execute()



