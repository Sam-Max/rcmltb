
from time import time
from bot import status_dict, status_dict_lock, LOGGER
from bot.helper.ext_utils.message_utils import editMessage
from bot.helper.ext_utils.misc_utils import ButtonMaker
from bot.helper.mirror_leech_utils.status_utils.status_utils import MirrorStatus
from bot.helper.mirror_leech_utils.status_utils.telegram_status import TelegramStatus

class TelegramDownloader:
    def __init__(self, file, client, message, path) -> None:
        self._client= client
        self._message= message 
        self.id= self._message.id
        self._file = file
        self._path= path

    async def download(self):
        file_name= self._file.file_name
        file_id = self._file.file_unique_id
        status= TelegramStatus(self._message, MirrorStatus.STATUS_DOWNLOADING, file_id)
        await status.create_empty_status(file_name)
        async with status_dict_lock:
            status_dict[self.id] = status
        try:
            media_path= await self._client.download_media(
                message= self._file,
                file_name= self._path,
                progress=status.start,
                progress_args=(file_name, time()))
        except Exception as e:
            LOGGER.error(str(e))
        async with status_dict_lock: 
            try:  
                del status_dict[self.id]
            except:
                pass
        return media_path

    