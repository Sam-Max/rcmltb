from asyncio import sleep
import os
import time
from bot import LOGGER, Bot, app, status_dict
from bot.utils.bot_utils.misc_utils import get_media_info, get_video_resolution
from bot.utils.bot_utils.screenshot import screenshot
from pyrogram import enums
from pyrogram.errors import FloodWait
from bot.utils.status_utils.misc_utils import MirrorStatus
from bot.utils.status_utils.telegram_status import TelegramStatus

VIDEO_SUFFIXES = ["mkv", "mp4", "mov", "wmv", "3gp", "mpg", "webm", "avi", "flv", "m4v", "gif"]

class TelegramUploader():
    def __init__(self, path, message, sender) -> None:
        self._client= app if app is not None else Bot
        self._path = path
        self._message= message 
        self._sender= sender
        self.current_time= time.time()

    async def upload(self):
        status= TelegramStatus(self._message)
        if os.path.isdir(self._path):
            for dirpath, _, files in os.walk(self._path):
                for file in sorted(files):
                    f_path = os.path.join(dirpath, file)
                    f_size = os.path.getsize(f_path)
                    if f_size == 0:
                        LOGGER.error(f"{f_size} size is zero, telegram don't upload zero size files")
                        continue
                    await self.__upload_file(f_path, status)
                    await sleep(1)
        else:
           await self.__upload_file(self._path, status)
           await sleep(1)  
        del status_dict[status.id] 
            
    async def __upload_file(self, up_path, status):
        try:
            if str(up_path).split(".")[-1] in VIDEO_SUFFIXES:
                    if not str(self._file).split(".")[-1] in ['mp4', 'mkv']:
                        path = str(up_path).split(".")[0] + ".mp4"
                        os.rename(self._file, path) 
                        self._file = str(up_path).split(".")[0] + ".mp4"
                    caption= str(up_path).split("/")[-1]  
                    duration= get_media_info(up_path)[0]
                    thumb_path = await screenshot(up_path, duration, self._sender)
                    width, height = get_video_resolution(thumb_path)
                    await self._client.send_video(
                        chat_id=self._sender,
                        video= up_path,
                        width=width,
                        height=height,
                        caption= f'`{caption}`',
                        parse_mode= enums.ParseMode.MARKDOWN ,
                        thumb= thumb_path,
                        supports_streaming=True,
                        duration= duration,
                        progress= status.progress,
                        progress_args=(
                            "Name: `{}`".format(caption),
                            f'**Status:** {MirrorStatus.STATUS_UPLOADING}',
                            self.current_time
                        )
                    )
            else:
                caption= str(up_path).split("/")[-1]  
                await self._client.send_document(
                    chat_id= self._sender,
                    document= up_path, 
                    caption= f'`{caption}`',
                    parse_mode= enums.ParseMode.MARKDOWN,
                    progress= status.progress,
                    progress_args=(
                        "**Name:** `{}`".format(caption),
                        "**Status:** Uploading...",
                        self.current_time
                    )
                )
        except FloodWait as f:
            sleep(f.value)
        except Exception as e:
            await self._message.edit(f"Failed to save: {self._path}")
        

   