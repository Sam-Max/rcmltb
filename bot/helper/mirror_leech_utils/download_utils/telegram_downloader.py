from time import time
from bot import (
    IS_PREMIUM_USER,
    bot,
    app,
    status_dict,
    config_dict,
    status_dict_lock,
    LOGGER,
)
from bot.helper.telegram_helper.message_utils import sendMessage, sendStatusMessage
from bot.helper.mirror_leech_utils.status_utils.tg_download_status import TelegramStatus


class TelegramDownloader:
    def __init__(self, file, client, listener, path, name=""):
        self.__client = client
        self.__listener = listener
        self.name = name
        self.gid = ""
        self.size = 0
        self.progress = 0
        self.downloaded_bytes = 0
        self.__file = file
        self.__path = path
        self.__start_time = time()
        self.__is_cancelled = False

    @property
    def download_speed(self):
        return self.downloaded_bytes / (time() - self.__start_time)

    async def __onDownloadStart(self, name, size, file_id):
        self.name = name
        self.size = size
        self.gid = file_id

        async with status_dict_lock:
            status_dict[self.__listener.uid] = TelegramStatus(
                self, size, self.__listener.message, self.gid
            )
        await sendStatusMessage(self.__listener.message)

        if not config_dict["NO_TASKS_LOGS"]:
            LOGGER.info(f"Download from Telegram: {name}")

    async def onDownloadProgress(self, current, total):
        if self.__is_cancelled:
            if IS_PREMIUM_USER:
                app.stop_transmission()
            else:
                bot.stop_transmission()
            return
        self.downloaded_bytes = current
        try:
            self.progress = current / self.size * 100
        except:
            pass

    async def download(self):
        if IS_PREMIUM_USER and not self.__listener.isSuperGroup:
            await sendMessage(
                "Use SuperGroup to download with User!", self.__listener.message
            )
            return
        if self.__file == None:
            return
        if self.name == "":
            name = (
                self.__file.file_name if hasattr(self.__file, "file_name") else "None"
            )
        else:
            name = self.name
            self.__path = self.__path + name
        size = self.__file.file_size
        gid = self.__file.file_unique_id
        await self.__onDownloadStart(name, size, gid)
        try:
            download = await self.__client.download_media(
                message=self.__file,
                file_name=self.__path,
                progress=self.onDownloadProgress,
            )
            if self.__is_cancelled:
                await self.__onDownloadError("Cancelled by user!")
                return
        except Exception as e:
            LOGGER.error(str(e))
            await self.__onDownloadError(str(e))
            return
        if download is not None:
            await self.__listener.onDownloadComplete()
        elif not self.__is_cancelled:
            await self.__onDownloadError("Internal error occurred")

    async def __onDownloadError(self, error):
        await self.__listener.onDownloadError(error)

    async def cancel_download(self):
        LOGGER.info(f"Cancelling download by user request")
        self.__is_cancelled = True
