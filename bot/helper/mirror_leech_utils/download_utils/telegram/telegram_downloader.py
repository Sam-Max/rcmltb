
from time import time
from bot import status_dict, status_dict_lock, LOGGER
from bot.helper.ext_utils.message_utils import editMessage
from bot.helper.mirror_leech_utils.status_utils.status_utils import MirrorStatus, get_bottom_status
from bot.helper.mirror_leech_utils.status_utils.telegram_status import TelegramStatus
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

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

        file_name= self._file.file_name
        status_type= MirrorStatus.STATUS_DOWNLOADING
        inlineKeyboard= InlineKeyboardMarkup([[InlineKeyboardButton('Cancel', callback_data=(f"cancel_telegram_{self.id}"))]])    
        status_msg= status.get_status_message(0, 0, 0, "", 0, file_name, status_type)
        await editMessage(status_msg, self._message, reply_markup=inlineKeyboard)
        try:
            media_path= await self._client.download_media(
                message= self._file,
                file_name= self._path,
                progress=status.progress,
                progress_args=(file_name, status_type, time(), inlineKeyboard))
        except Exception as e:
            LOGGER.error(str(e))
        async with status_dict_lock: 
            try:  
                del status_dict[self.id]
            except:
                pass
        return media_path

