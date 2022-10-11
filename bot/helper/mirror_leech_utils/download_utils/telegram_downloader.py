
from time import time
from bot import Bot, status_dict, status_dict_lock, LOGGER
from bot.helper.ext_utils.message_utils import sendStatusMessage
from bot.helper.mirror_leech_utils.status_utils.tg_download_status import TelegramStatus

class TelegramDownloader:
    def __init__(self, file, client, listener, path) -> None:
        self._client= client
        self.__listener = listener
        self.name = ""
        self.size = 0
        self.progress = 0
        self.downloaded_bytes = 0
        self.__start_time = time()
        self.__is_cancelled = False
        self.__file = file
        self.__path= path

    @property
    def download_speed(self):
        return self.downloaded_bytes / (time() - self.__start_time)

    async def onDownloadProgress(self, current, total):
        if self.__is_cancelled:
            Bot.stop_transmission()
            return
        self.downloaded_bytes = current
        try:
            self.progress = current / self.size * 100
        except ZeroDivisionError:
            pass

    async def download(self):
        self.name= self.__file.file_name
        self.size = self.__file.file_size
        gid = self.__file.file_unique_id
        async with status_dict_lock:
            status_dict[self.__listener.uid] = TelegramStatus(self, self.__listener.message, gid)
        await sendStatusMessage(self.__listener.message)
        try:
            download= await self._client.download_media(
                message= self.__file,
                file_name= self.__path,
                progress= self.onDownloadProgress)
            if self.__is_cancelled:
                await self.__onDownloadError("Cancelled by user")
            if download is not None:
                await self.__listener.onDownloadComplete()
        except Exception as e:
            await self.__onDownloadError(str(e))

    async def __onDownloadError(self, error):
        await self.__listener.onDownloadError(error) 

    def cancel_download(self):
        LOGGER.info(f'Cancelling download by user request')
        self.__is_cancelled = True

    

    