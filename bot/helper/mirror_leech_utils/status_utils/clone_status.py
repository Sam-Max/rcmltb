from asyncio import sleep
from time import time
from bot import EDIT_SLEEP_SECS
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.helper.ext_utils.bot_utils import get_readable_time
from bot.helper.ext_utils.human_format import get_readable_file_size
from bot.helper.ext_utils.message_utils import editMessage, sendMarkup, sendMessage
from bot.helper.mirror_leech_utils.status_utils.status_utils import MirrorStatus, get_bottom_status, get_progress_bar_string


class CloneStatus:
    def __init__(self, obj, size, message, gid):
        self.__obj = obj
        self.__size = size
        self.__gid = gid
        self.message = message

    async def start(self):
        sleeps= False
        start = time()
        data = "cancel {}".format(self.gid())
        status_msg = self.get_status_message_text()
        rmsg= await sendMarkup(status_msg, self.message, reply_markup=(InlineKeyboardMarkup([
                            [InlineKeyboardButton('Cancel', callback_data=data.encode("UTF-8"))]])))
        while True:
            sleeps = True
            status_msg  = self.get_status_message_text()
            if time() - start > EDIT_SLEEP_SECS:
                await editMessage(status_msg, rmsg, reply_markup=(InlineKeyboardMarkup([
                                [InlineKeyboardButton('Cancel', callback_data=data.encode("UTF-8"))]]))) 
                if sleeps:
                    if self.__obj.is_cancelled:
                        return rmsg
                    if self.__obj.is_completed:
                        return rmsg
                    sleeps = False
                    await sleep(1)
    
    def get_status_message_text(self):
        msg = f"<code>{str(self.name())}</code>"
        msg += f"\n<b>Status:</b> {MirrorStatus.STATUS_CLONING}"
        msg += f"\n{get_progress_bar_string(self.processed_bytes(), self.size_raw())} {self.progress()}"
        msg += f"\n<b>Processed:</b> {get_readable_file_size(self.processed_bytes())} of {self.size()}"
        msg += f"\n<b>Speed:</b> {self.speed()} | <b>ETA:</b> {self.eta()}\n"
        msg += get_bottom_status()
        return msg

    def get_status_msg(self):
        return self.get_status_message_text()

    def processed_bytes(self):
        return self.__obj.transferred_size

    def size_raw(self):
        return self.__size

    def size(self):
        return get_readable_file_size(self.__size)

    def status(self):
        return MirrorStatus.STATUS_CLONING

    def name(self):
        return self.__obj.name

    def gid(self) -> str:
        return self.__gid

    def progress_raw(self):
        try:
            return self.__obj.transferred_size / self.__size * 100
        except:
            return 0

    def progress(self):
        return f'{round(self.progress_raw(), 2)}%'

    def speed_raw(self):
        """
        :return: Download speed in Bytes/Seconds
        """
        return self.__obj.cspeed()

    def speed(self):
        return f'{get_readable_file_size(self.speed_raw())}/s'

    def eta(self):
        try:
            seconds = (self.__size - self.__obj.transferred_size) / self.speed_raw()
            return f'{get_readable_time(seconds)}'
        except:
            return '-'

    def download(self):
        return self.__obj

    def cancel_download(self):
       self.__obj.cancel_download()
