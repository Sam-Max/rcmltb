# Source: https://github.com/anasty17/mirror-leech-telegram-bot/
# Adapted for asyncio framework and pyrogram library

from pathlib import Path
from bot import LOGGER, botloop
from bot.helper.ext_utils.bot_utils import setInterval
from bot import status_dict, status_dict_lock
from bot.helper.ext_utils.message_utils import sendMessage, sendStatusMessage
from bot.helper.mirror_leech_utils.status_utils.mega_status import MegaDownloadStatus
from megasdkrestclient import MegaSdkRestClient, constants


class MegaDownloader():
    POLLING_INTERVAL = 3

    def __init__(self, link, listener):
        super().__init__()
        self._link = link
        self.__name = ''
        self.__gid = ''
        self.__mega_client = MegaSdkRestClient('http://localhost:6090')
        self.__listener = listener
        self.__periodic= None
        self.__downloaded_bytes = 0
        self.__progress = 0
        self.__size = 0

    @property
    def progress(self):
        return self.__progress

    @property
    def downloaded_bytes(self):
        return self.__downloaded_bytes

    @property
    def size(self):
        return self.__size

    @property
    def gid(self):
        return self.__gid

    @property
    def name(self):
        return self.__name

    @property
    def download_speed(self):
        if self.gid is not None:
            return self.__mega_client.getDownloadInfo(self.gid)['speed']

    async def __onDownloadStart(self, name, size, gid):
        self.__periodic = setInterval(self.POLLING_INTERVAL, self.__onInterval)
        async with status_dict_lock:
            status_dict[self.__listener.uid] = MegaDownloadStatus(self, self.__listener)
            self.__name = name
            self.__size = size
            self.__gid = gid
        self.__listener.onDownloadStart()
        await sendStatusMessage(self.__listener.message)

    async def execute(self, path):
        Path(path).mkdir(parents=True, exist_ok=True)
        LOGGER.info("MegaDownload Started...")
        try:
            dl = await botloop.run_in_executor(None, self.__mega_client.addDl, self._link, path)
        except Exception as er:
            return await sendMessage(str(er), self.__listener.message)
        gid = dl["gid"]
        info = await botloop.run_in_executor(None, self.__mega_client.getDownloadInfo, gid)
        name = info['name']
        size = info['total_length']
        async with status_dict_lock:  
            status_dict[self.__listener.uid] = MegaDownloadStatus(self, self.__listener)
        await self.__onDownloadStart(name, size, gid)
        LOGGER.info(f'Mega download started with gid: {gid}')

    async def __onDownloadError(self, error):
        await self.__listener.onDownloadError(error)

    async def __onDownloadComplete(self):
        await self.__listener.onDownloadComplete()

    def __onDownloadProgress(self, current, total):
            self.__downloaded_bytes = current
            try:
                self.__progress = current / total * 100
            except ZeroDivisionError:
                self.__progress = 0    

    async def __onInterval(self):
        dlInfo = self.__mega_client.getDownloadInfo(self.gid)
        name = dlInfo['name']
        if dlInfo['state'] in [constants.State.TYPE_STATE_COMPLETED, constants.State.TYPE_STATE_CANCELED, 
            constants.State.TYPE_STATE_FAILED] and self.__periodic is not None:
            self.__periodic.cancel()
        if dlInfo['state'] == constants.State.TYPE_STATE_COMPLETED:
            await self.__onDownloadComplete()
            return
        if dlInfo['state'] == constants.State.TYPE_STATE_CANCELED:
            LOGGER.info(f"Cancelling Download: {name}, cause: 'Download stopped by user!'")
            await self.__onDownloadError('Download stopped by user!')
            return
        if dlInfo['state'] == constants.State.TYPE_STATE_FAILED:
            LOGGER.info(f"Cancelling Download: {name}, cause: {dlInfo['error_string']}'")
            await self.__onDownloadError(dlInfo['error_string'])
            return
        self.__onDownloadProgress(dlInfo['completed_length'], dlInfo['total_length'])

    def cancel_download(self):
        LOGGER.info(f'Cancelling download on user request: {self.gid}')
        self.__mega_client.cancelDl(self.gid)