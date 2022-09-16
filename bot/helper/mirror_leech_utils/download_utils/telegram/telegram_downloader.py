
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
        status= TelegramStatus(self._message)
        async with status_dict_lock:
            status_dict[self.id] = status
        file_name= self._file.file_name
        status_type= MirrorStatus.STATUS_DOWNLOADING
        await self.__create_empty_status(file_name, status, status_type)
        try:
            media_path= await self._client.download_media(
                message= self._file,
                file_name= self._path,
                progress=status.start,
                progress_args=(file_name, status_type, time()))
        except Exception as e:
            LOGGER.error(str(e))
        async with status_dict_lock: 
            try:  
                del status_dict[self.id]
            except:
                pass
        return media_path

    async def __create_empty_status(self, file_name, status, status_type ):
        button= ButtonMaker()
        button.cb_buildbutton('Cancel', data=(f"cancel_telegram_{self.id}"))
        status_msg= status.get_status_text(0, 0, 0, "", 0, file_name, status_type)
        await editMessage(status_msg, self._message, reply_markup=button.build_menu(1))