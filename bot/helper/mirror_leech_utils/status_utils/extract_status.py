from time import time
from bot import DOWNLOAD_DIR, LOGGER
from bot.helper.ext_utils.human_format import get_readable_file_size
from bot.helper.ext_utils.message_utils import editMessage
from bot.helper.ext_utils.zip_utils import get_path_size
from bot.helper.mirror_leech_utils.status_utils.status_utils import MirrorStatus, get_bottom_status

class ExtractStatus:
    def __init__(self, name, size, message, listener):
        self.__user_message= message
        self.__id = self.__user_message.id
        self.__name = name
        self.__size= size
        self.__start_time = time()
        self.__listener= listener
        self.__status_msg = ""

    def get_status_msg(self):
        return self.__status_msg  

    def speed_raw(self):
        return self.processed_bytes() / (time() - self.__start_time)

    def speed(self):
        return '0.0/s'

    def progress_raw(self):
        try:
            return self.processed_bytes() / self.__size * 100
        except:
            return 0

    def progress_string(self):
        return f'{round(self.progress_raw(), 2)}%'

    def processed_bytes(self):
        return get_path_size(f"{DOWNLOAD_DIR}{self.__name}") - self.__size

    def eta(self):
        return '-'

    def status(self):
        return MirrorStatus.STATUS_EXTRACTING

    async def create_message(self):
        msg = f'<b>Name:</b> {self.__name}\n'
        msg += f'<b>Status:</b> {self.status()}\n'
        msg += f"<b>Size:</b> {get_readable_file_size(self.__size)}\n"
        msg += f'<b>Speed:</b> {self.speed()} | <b>ETA:</b> {self.eta()}\n'
        msg += get_bottom_status()
        self._status_msg= msg
        await editMessage(self._status_msg, self.__user_message)

    def cancel_download(self):
        LOGGER.info(f'Cancelling Extract: {self.__name}')
        if self.__listener.suproc is not None:
            self.__listener.suproc.kill()
        LOGGER.info('Extracting stopped!')
