from asyncio import sleep
from time import time
from bot import DOWNLOAD_DIR, LOGGER
from pyrogram.errors.exceptions import FloodWait, MessageNotModified
from bot.helper.ext_utils.human_format import get_readable_file_size
from bot.helper.ext_utils.zip_utils import get_path_size
from bot.helper.mirror_leech_utils.status_utils.status_utils import MirrorStatus, get_bottom_status

class ZipStatus:
    def __init__(self, name, size, message, listener):
        self.__name = name
        self.__size= size
        self.__user_message= message
        self.id = self.__user_message.id
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
        return MirrorStatus.STATUS_ARCHIVING

    async def create_message(self):
        msg = f'**Name:** {self.__name}\n'
        msg += f'**Status:** {self.status()}\n'
        msg += f"**Size:** {get_readable_file_size(self.__size)}\n"
        msg += f'**Speed:** {self.speed()} | **ETA:** {self.eta()}\n'
        msg += get_bottom_status()
        self._status_msg= msg

        try:
            await self.__user_message.edit(text= self._status_msg)
        except FloodWait as fw:
            LOGGER.warning(f"FloodWait : Sleeping {fw.value}s")
            await sleep(fw.value)
        except MessageNotModified:
            await sleep(1)
        except Exception:
            await sleep(1)

    def cancel_download(self):
        LOGGER.info(f'Cancelling Archive: {self.__name}')
        if self.__listener.suproc is not None:
            self.__listener.suproc.kill()
        LOGGER.info('Archiving stopped!')
