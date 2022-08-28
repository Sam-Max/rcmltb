
import time
from bot import status_dict, status_dict_lock, LOGGER
from bot.utils.status_utils.status_utils import MirrorStatus
from bot.utils.status_utils.telegram_status import TelegramStatus


class TelegramDownloader:
    def __init__(self, file, client, message, path) -> None:
        self._client= client
        self._file = file
        self._message= message 
        self.id= self._message.id
        self._path= path

    async def download(self):
        status= TelegramStatus(self._message)
        async with status_dict_lock:
            status_dict[self.id] = status
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
        async with status_dict_lock: 
            try:  
                del status_dict[self.id]
            except:
                pass
        return media_path

