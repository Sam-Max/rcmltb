from asyncio import sleep
from time import time
from bot import DOWNLOAD_DIR, EDIT_SLEEP_SECS, status_dict
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.helper.ext_utils.bot_utils import get_readable_time
from bot.helper.ext_utils.human_format import get_readable_file_size
from bot.helper.ext_utils.message_utils import editMessage
from bot.helper.ext_utils.zip_utils import get_path_size
from bot.helper.mirror_leech_utils.status_utils.status_utils import MirrorStatus, get_bottom_status, get_progress_bar_string


class YtDlpDownloadStatus:
    def __init__(self, obj, message, gid):
        self.__obj = obj
        self.message = message
        self.__id = self.message.id
        self.__gid = gid

    async def start(self):
        sleeps= False
        start = time()
        data = "cancel {}".format(self.gid())
        status_msg = self.get_status_message_text()
        await editMessage(status_msg, self.message, reply_markup=(InlineKeyboardMarkup([
                            [InlineKeyboardButton('Cancel', callback_data=data.encode("UTF-8"))]])))
        while True:
            sleeps = True
            status_msg  = self.get_status_message_text()
            if time() - start > EDIT_SLEEP_SECS:
                await editMessage(status_msg, self.message, reply_markup=(InlineKeyboardMarkup([
                                [InlineKeyboardButton('Cancel', callback_data=data.encode("UTF-8"))]]))) 
                if sleeps:
                    if self.__obj.is_cancelled:
                        del status_dict[self.__id] 
                        await editMessage(f"{self.__obj.error_message}", self.message)
                        return False
                    if self.__obj.is_completed:
                        #del status_dict[self.__id] 
                        return True
                    sleeps = False
                    await sleep(1)

    def get_status_message_text(self):
        msg = f"<code>{str(self.name())}</code>"
        msg += f"\n<b>Status:</b> {MirrorStatus.STATUS_DOWNLOADING}"
        msg += f"\n{get_progress_bar_string(self.processed_bytes(), self.size_raw())} {self.progress()}"
        msg += f"\n<b>Processed:</b> {get_readable_file_size(self.processed_bytes())} of {self.size()}"
        msg += f"\n<b>Speed:</b> {self.speed()} | <b>ETA:</b> {self.eta()}\n"
        msg += get_bottom_status()
        return msg

    def get_status_msg(self):
        return self.get_status_message_text()

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

    def cancel_download(self):
       self.__obj.cancel_download()

