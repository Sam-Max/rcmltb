from asyncio import sleep
from os import walk, rename, path as ospath
import time
from bot import LOGGER, Bot, app, status_dict, status_dict_lock
from bot.utils.bot_utils.misc_utils import get_media_info, get_video_resolution
from bot.utils.bot_utils.screenshot import screenshot
from pyrogram import enums
from pyrogram.errors import FloodWait
from bot.utils.status_utils.status_utils import MirrorStatus
from bot.utils.status_utils.telegram_status import TelegramStatus

VIDEO_SUFFIXES = ["mkv", "mp4", "mov", "wmv", "3gp", "mpg", "webm", "avi", "flv", "m4v", "gif"]

class TelegramUploader():
    def __init__(self, path, message, sender) -> None:
        self._client= app if app is not None else Bot
        self._path = path
        self._message= message 
        self.id= self._message.id
        self._sender= sender
        self.current_time= time.time()

    async def upload(self):
        async with status_dict_lock:
            status_dict[self.id] = self
        status= TelegramStatus(self._message)
        if ospath.isdir(self._path):
            for dirpath, _, files in walk(self._path):
                for file in sorted(files):
                    f_path = ospath.join(dirpath, file)
                    f_size = ospath.getsize(f_path)
                    if f_size == 0:
                        LOGGER.error(f"{f_size} size is zero, telegram don't upload zero size files")
                        continue
                    await self.__upload_file(f_path, status)
                    await sleep(1)
        else:
           await self.__upload_file(self._path, status)
           await sleep(1)  
        async with status_dict_lock:   
            del status_dict[self.id] 
            
    async def __upload_file(self, up_path, status):
        try:
            if str(up_path).split(".")[-1] in VIDEO_SUFFIXES:
                    if not str(up_path).split(".")[-1] in ['mp4', 'mkv']:
                        path = str(up_path).split(".")[0] + ".mp4"
                        rename(up_path, path) 
                        up_path = path
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
                        parse_mode= enums.ParseMode.MARKDOWN,
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
        

   