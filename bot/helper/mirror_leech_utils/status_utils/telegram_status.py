from asyncio import sleep
from math import floor
import time
from bot import Bot
from bot.helper.ext_utils.human_format import human_readable_bytes, human_readable_timedelta
from bot.helper.ext_utils.message_utils import editMessage
from bot.helper.ext_utils.misc_utils import ButtonMaker
from bot.helper.mirror_leech_utils.status_utils.status_utils import MirrorStatus, get_bottom_status

FINISHED_PROGRESS_STR = "■"
UN_FINISHED_PROGRESS_STR = "□"

class TelegramStatus:
    def __init__(self, user_message, status_type, gid):
        self.message = user_message
        self.id = self.message.id
        self.status_msg= None
        self._status_msg_text= ""
        self._gid= gid
        self.is_cancelled = False
        self.status_type= status_type
        
    async def create_empty_status(self, file_name):
        button= ButtonMaker()
        button.cb_buildbutton('Cancel', data=(f"cancel {self._gid}"))
        self._status_msg_text= self.get_status_text(0, 0, 0, "", 0, file_name)
        self.message = await editMessage(self._status_msg_text, self.message, reply_markup=button.build_menu(1))

    async def start(self, current, total, name, current_time):
        now = time.time()
        diff = now - current_time
        button= ButtonMaker()
        button.cb_buildbutton('Cancel', data=(f"cancel {self._gid}"))   
        
        if self.is_cancelled:
            await editMessage('Download cancelled', self.message)
            await sleep(1.5) 
            Bot.stop_transmission()
        
        if round(diff % 10.00) == 0 or current == total:
            percentage = current * 100 / total
            speed = current / diff
            elapsed_time = round(diff) * 1000
            time_to_completion = round((total - current) / speed) * 1000
            estimated_total_time = elapsed_time + time_to_completion
            elapsed_time = human_readable_timedelta(elapsed_time)
            estimated_total_time = human_readable_timedelta(estimated_total_time)

            self._status_msg_text = self.get_status_text(current, total, speed, estimated_total_time, percentage, name)
            self.status_msg = await editMessage(self._status_msg_text, self.message, reply_markup= button.build_menu(1))

    def status(self):
        if self.status_type == MirrorStatus.STATUS_DOWNLOADING:
            return MirrorStatus.STATUS_DOWNLOADING
        else:
            return MirrorStatus.STATUS_UPLOADING

    def get_status_msg(self):
        return self._status_msg_text

    def get_status_text(self, current, total, speed, estimated_total_time, percentage, name):
        progress = "{0}{1}\n**P:** {2}%".format(
                ''.join([FINISHED_PROGRESS_STR for i in range(floor(percentage / 10))]),
                ''.join([UN_FINISHED_PROGRESS_STR for i in range(10 - floor(percentage / 10))]),
                round(percentage, 2))

        return "**Name**:`{0}`\n**Status:** {1}\n{2}\n**Downloaded:** {3} of {4}\n**Speed**: {5} | **ETA:** {6}\n {7}".format(
            name,
            self.status_type,
            progress,
            human_readable_bytes(current),
            human_readable_bytes(total),
            human_readable_bytes(speed),
            estimated_total_time if estimated_total_time != '' else "0 s",
            get_bottom_status())

    def gid(self):
        return self._gid

    def cancel_download(self):
        self.is_cancelled = True

