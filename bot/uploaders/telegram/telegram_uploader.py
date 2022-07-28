#Adapted from:
#Github.com/Vasusen-code

from asyncio import sleep
import os
from random import randrange
import time
from bot import GLOBAL_TG_DOWNLOADER, Bot, app, LOGGER
from bot.utils.bot_utils.misc_utils import get_media_info, get_video_resolution
from bot.utils.status_utils.progress_for_pyrogram import progress_for_pyrogram
from bot.utils.bot_utils.screenshot import screenshot
from pyrogram import enums

VIDEO_SUFFIXES = ["mkv", "mp4", "mov", "wmv", "3gp", "mpg", "webm", "avi", "flv", "m4v", "gif"]

class TelegramUploader():
    def __init__(self, file, message, sender) -> None:
        self.id = self.__create_id(8)
        self._client= app if app is not None else Bot
        self._file = file
        self._message= message 
        self._sender= sender
        self._cancelled= False

    def __create_id(self, count):
        map = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        id = ''
        i = 0
        while i < count:
            rnd = randrange(len(map))
            id += map[rnd]
            i += 1
        return id

    async def upload(self):
        LOGGER.info("Uploading...")
        LOGGER.info(self._client.name)
        GLOBAL_TG_DOWNLOADER.add(self)
        c_time = time.time()
        try:
            if str(self._file).split(".")[-1] in VIDEO_SUFFIXES:
                    if not str(self._file).split(".")[-1] in ['mp4', 'mkv']:
                        path = str(self._file).split(".")[0] + ".mp4"
                        os.rename(self._file, path) 
                        self._file = str(self._file).split(".")[0] + ".mp4"
                    caption= str(self._file).split("/")[-1]  
                    duration= get_media_info(self._file)[0]
                    thumb_path = await screenshot(self._file, duration, self._sender)
                    width, height = get_video_resolution(thumb_path)
                    await self._client.send_video(
                        chat_id=self._sender,
                        video= self._file,
                        width=width,
                        height=height,
                        caption= f'`{caption}`',
                        parse_mode= enums.ParseMode.MARKDOWN ,
                        thumb= thumb_path,
                        supports_streaming=True,
                        duration= duration,
                        progress=self.__onDownloadProgress,
                        progress_args=(
                            "Name: `{}`".format(caption),
                            '**Status:** Uploading...',
                            self._message,
                            self.id,
                            c_time
                        )
                    )
            else:
                caption= str(self._file).split("/")[-1]  
                await self._client.send_document(
                    chat_id= self._sender,
                    document= self._file, 
                    caption= f'`{caption}`',
                    parse_mode= enums.ParseMode.MARKDOWN,
                    progress=self.__onDownloadProgress,
                    progress_args=(
                        "**Name:** `{}`".format(caption),
                        "**Status:** Uploading...",
                        self._message,
                        self.id,
                        c_time
                    )
                )
            await self._message.delete() 
        except Exception as e:
            LOGGER.info(e)
            await self._message.delete() 
            file_name= str(self._file).split("/")[-1]
            await self._client.send_message(self._sender, f"Failed to save: {file_name} - cause: {e}")  
        GLOBAL_TG_DOWNLOADER.remove(self)  

    async def __onDownloadProgress(self, current, total, name, status, mess_age, id, c_time):
          if self._cancelled:
               await sleep(1.5)  
               await self._message.delete() 
               await self._client.send_message(self._sender, 'Upload cancelled!!')
               Bot.stop_transmission()
          await progress_for_pyrogram(current, total, name, status , mess_age, id, c_time)

    def cancel_download(self):
        self._cancelled = True