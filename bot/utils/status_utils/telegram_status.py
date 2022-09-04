from asyncio import sleep
from math import floor
import time
from bot import LOGGER, Bot, status_dict, status_dict_lock
from bot.utils.status_utils.status_utils import get_bottom_status, humanbytes, time_formatter
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors.exceptions import FloodWait, MessageNotModified

FINISHED_PROGRESS_STR = "■"
UN_FINISHED_PROGRESS_STR = "□"

class TelegramStatus:
     def __init__(self, user_message):
        self._user_message = user_message
        self.id = self._user_message.id
        self.cancelled = False
        self._status_msg = ""

     def get_status_msg(self):
         return self._status_msg

     async def progress(self, current, total, name, status, current_time):
         now = time.time()
         diff = now - current_time
         
         if self.cancelled:
            await self._user_message.edit('Download cancelled')   
            await sleep(1.5) 
            async with status_dict_lock:
                del status_dict[self.id]
            Bot.stop_transmission()
           
         if round(diff % 10.00) == 0 or current == total:
            percentage = current * 100 / total
            speed = current / diff
            elapsed_time = round(diff) * 1000
            time_to_completion = round((total - current) / speed) * 1000
            estimated_total_time = elapsed_time + time_to_completion
            elapsed_time = time_formatter(milliseconds=elapsed_time)
            estimated_total_time = time_formatter(milliseconds=estimated_total_time)

            progress = "{0}{1}\n**P:** {2}%".format(
                  ''.join([FINISHED_PROGRESS_STR for i in range(floor(percentage / 10))]),
                  ''.join([UN_FINISHED_PROGRESS_STR for i in range(10 - floor(percentage / 10))]),
                  round(percentage, 2))

            self._status_msg = "{0}\n{1}\n{2}\n**Downloaded:** {3} of {4}\n**Speed**: {5} | **ETA:** {6}\n {7}".format(
                  name,
                  status,
                  progress,
                  humanbytes(current),
                  humanbytes(total),
                  humanbytes(speed),
                  estimated_total_time if estimated_total_time != '' else "0 s",
                  get_bottom_status())
            
            try:
                  await self._user_message.edit(self._status_msg,
                  reply_markup=(InlineKeyboardMarkup([[InlineKeyboardButton('Cancel', callback_data=(f"cancel_telegram_{self.id}"))]])))  
            except FloodWait as fw:
                  LOGGER.warning(f"FloodWait : Sleeping {fw.value}s")
                  await sleep(fw.value)
            except MessageNotModified:
                  await sleep(1)



