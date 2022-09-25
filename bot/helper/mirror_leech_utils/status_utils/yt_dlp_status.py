from asyncio import sleep
from time import time
from bot import DOWNLOAD_DIR, EDIT_SLEEP_SECS
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot import status_dict, status_dict_lock
from bot.helper.ext_utils.bot_utils import get_readable_time
from bot.helper.ext_utils.human_format import get_readable_file_size
from bot.helper.ext_utils.message_utils import editMarkup, editMessage
from bot.helper.ext_utils.zip_utils import get_path_size
from bot.helper.mirror_leech_utils.status_utils.status_utils import MirrorStatus, get_bottom_status


class YtDlpDownloadStatus:
    def __init__(self, obj, message, gid):
        self.__obj = obj
        self.__id = message.id
        self.__gid = gid
        self.message = message
        self.__status_msg= None

    def get_status_msg(self):
        return self.__status_msg

    async def start(self):
        sleeps= False
        start = time()
        data = "cancel {}".format(self.gid())
        status_msg = self.create_update_message()
        await editMarkup(status_msg, self.message, reply_markup=(InlineKeyboardMarkup([
                            [InlineKeyboardButton('Cancel', callback_data=data.encode("UTF-8"))]])))
        while True:
            sleeps = True
            status_msg  = self.create_update_message()
            self.__status_msg = status_msg 
            if time() - start > EDIT_SLEEP_SECS:
                await editMarkup(status_msg, self.message, reply_markup=(InlineKeyboardMarkup([
                                [InlineKeyboardButton('Cancel', callback_data=data.encode("UTF-8"))]]))) 
                if sleeps:
                    if self.__obj.is_cancelled:
                        async with status_dict_lock:
                            del status_dict[self.__id]
                        await editMessage(f"{self.__obj.error_message}", self.message)
                        return
                    if self.__obj.is_completed:
                        return 
                    sleeps = False
                    await sleep(1)

    def create_update_message(self):
        msg = f"<code>{str(self.name())}</code>"
        msg += f"\n<b>Status:</b> {MirrorStatus.STATUS_DOWNLOADING}"
        msg += f"\n{self.get_progress_bar_string()} {self.progress()}"
        msg += f"\n<b>Processed:</b> {get_readable_file_size(self.processed_bytes())} of {self.size()}"
        msg += f"\n<b>Speed:</b> {self.speed()} | <b>ETA:</b> {self.eta()}\n"
        msg += get_bottom_status()
        return msg

    def cancel_download(self):
       self.__obj.cancel_download()

    def status(self):
        return MirrorStatus.STATUS_DOWNLOADING

    def gid(self):
        return self.__gid

    def name(self):
        return self.__obj.name

    def processed_bytes(self):
        if self.__obj.downloaded_bytes != 0:
          return self.__obj.downloaded_bytes
        else:
          return get_path_size(f"{DOWNLOAD_DIR}{self.__id}")

    def size_raw(self):
        return self.__obj.size

    def size(self):
        return get_readable_file_size(self.size_raw())

    def progress_raw(self):
        return self.__obj.progress

    def progress(self):
        return f'{round(self.progress_raw(), 2)}%'

    def speed_raw(self):
        """
        :return: Download speed in Bytes/Seconds
        """
        return self.__obj.download_speed

    def speed(self):
        return f'{get_readable_file_size(self.speed_raw())}/s'

    def eta(self):
        if self.__obj.eta != '-':
            return f'{get_readable_time(self.__obj.eta)}'
        try:
            seconds = (self.size_raw() - self.processed_bytes()) / self.speed_raw()
            return f'{get_readable_time(seconds)}'
        except:
            return '-'

    def get_progress_bar_string(self):
        completed = self.processed_bytes() / 8
        total = self.size_raw() / 8
        p = 0 if total == 0 else round(completed * 100 / total)
        p = min(max(p, 0), 100)
        cFull = p // 8
        p_str = '■' * cFull
        p_str += '□' * (12 - cFull)
        p_str = f"[{p_str}]"
        return p_str
