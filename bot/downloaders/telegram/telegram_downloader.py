
from asyncio import sleep
from random import randrange
import time
from bot import GLOBAL_TG_DOWNLOADER, LOGGER, Bot
from bot.utils.status_utils.progress_for_pyrogram import progress_for_pyrogram


class TelegramDownloader:
    def __init__(self, file, client, mess_age, path) -> None:
        self.id = self.__create_id(8)
        self._client= client
        self._file = file
        self._mess_age= mess_age 
        self._path= path
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

    async def download(self):
        GLOBAL_TG_DOWNLOADER.add(self)
        try:
            media_path= await self._client.download_media(
                message= self._file,
                file_name= self._path,
                progress=self.__onDownloadProgress,
                progress_args=(
                "**Name**: `{}`".format(self._file.file_name),
                "**Status:** Downloading...",
                self._mess_age, 
                self.id,
                time.time()
                ))
        except Exception as e:
            LOGGER.error(str(e))
        GLOBAL_TG_DOWNLOADER.remove(self)
        return media_path

    async def __onDownloadProgress(self, current, total, name, status, mess_age, id, c_time):
          if self._cancelled:
               await sleep(1.5)  
               await mess_age.edit('Download cancelled!!') 
               Bot.stop_transmission()
          await progress_for_pyrogram(current, total, name, status , mess_age, id, c_time)

    def cancel_download(self):
        self._cancelled = True
