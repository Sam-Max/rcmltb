
import time
from bot import GLOBAL_TG_DOWNLOADER, LOGGER
from bot.utils.status_utils.misc_utils import MirrorStatus
from bot.utils.status_utils.telegram_status import TelegramStatus


class TelegramDownloader:
    def __init__(self, file, client, mess_age, path) -> None:
        self._client= client
        self._file = file
        self._mess_age= mess_age 
        self._path= path

    async def download(self):
        status= TelegramStatus(self._mess_age)
        GLOBAL_TG_DOWNLOADER.add(status)
        try:
            media_path= await self._client.download_media(
                message= self._file,
                file_name= self._path,
                progress=status.progress,
                progress_args=(
                "**Name**: `{}`".format(self._file.file_name),
                f'**Status:** {MirrorStatus.STATUS_DOWNLOADING}',
                time.time()
                ))
        except Exception as e:
            LOGGER.error(str(e))
        GLOBAL_TG_DOWNLOADER.remove(status)
        return media_path

