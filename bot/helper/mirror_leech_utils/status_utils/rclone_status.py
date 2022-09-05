from asyncio import sleep
from math import floor
from os.path import basename
import re
import time
from telethon.errors import FloodWaitError
from telethon import Button
from bot import EDIT_SLEEP_SECS, LOGGER, status_dict, status_dict_lock
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.helper.ext_utils.message_utils import editMessage

from bot.helper.mirror_leech_utils.status_utils.status_utils import MirrorStatus, get_bottom_status



class RcloneStatus:
     def __init__(self, process, message, path=""):
        self._process = process
        self._message = message
        self.id = self._message.id
        self._path= path
        self._status_msg= ""
        self.cancelled = False

     def get_status_msg(self):
         return self._status_msg     

     async def progress(self, status_type, client_type):
        async with status_dict_lock:
            status_dict[self.id] = self
        blank = 0
        sleeps = False
        start = time.time()

        while True:
            data = self._process.stdout.readline().decode()
            data = data.strip()
            mat = re.findall('Transferred:.*ETA.*', data)

            if mat is not None and len(mat) > 0:
                sleeps = True
                nstr = mat[0].replace('Transferred:', '')
                nstr = nstr.strip()
                nstr = nstr.split(',')
                percent = nstr[1].strip('% ')
                try:
                    percentage = int(percent)
                except:
                    percentage = 0
                prg = self.__get_progress_bar(percentage)

                if status_type == MirrorStatus.STATUS_UPLOADING:
                    self._status_msg = '**Name:** `{}`\n**Status:** {}\n{}\n**Uploaded:** {}\n**Speed:** {} | **ETA:** {}\n'.format(
                              basename(self._path), status_type, prg, nstr[0], nstr[2], nstr[3].replace('ETA', ''))
                if status_type == MirrorStatus.STATUS_CLONING:
                    self._status_msg = '**Name:** `{}`\n**Status:** {}\n{}\n**Downloaded:** {}\n**Speed:** {} | **ETA:** {}\n'.format(
                                        basename(self._path), status_type, prg, nstr[0], nstr[2], nstr[3].replace('ETA', ''))
                if status_type == MirrorStatus.STATUS_DOWNLOADING:
                    self._status_msg = '**Name:** `{}`\n**Status:** {}\n{}\n**Downloaded:** {}\n**Speed:** {} | **ETA:** {}\n'.format(
                                        basename(self._path), status_type, prg, nstr[0], nstr[2], nstr[3].replace('ETA', ''))
                if status_type == MirrorStatus.STATUS_COPYING:
                    self._status_msg = '**Status:** {}\n{}\n**Copied:** {}\n**Speed:** {} | **ETA:** {}\n'.format(
                                            status_type, prg, nstr[0], nstr[2], nstr[3].replace('ETA', ''))
                self._status_msg += get_bottom_status()
                
                if time.time() - start > EDIT_SLEEP_SECS:
                        start = time.time()
                        if client_type == 'pyrogram':
                            await editMessage(self._status_msg, self._message, reply_markup= InlineKeyboardMarkup([
                            [InlineKeyboardButton('Cancel', callback_data=f"cancel_rclone_{self.id}")]
                            ]))
                        if client_type == 'telethon':
                              try:
                                   await self._message.edit(text=self._status_msg, 
                                   buttons= [[Button.inline("Cancel", f"cancel_rclone_{self.id}".encode('UTF-8'))]])
                              except FloodWaitError as fw:
                                   LOGGER.warning(f"FloodWait : Sleeping {fw.seconds}s")
                                   await sleep(fw.value)
                              except:
                                  await sleep(1)
            
            if data == '':
                blank += 1
                if blank == 20:
                    async with status_dict_lock:     
                        del status_dict[self.id]
                    return True
            else:
                blank = 0

            if sleeps:
                sleeps = False
                if self.cancelled:
                    async with status_dict_lock:
                        del status_dict[self.id] 
                    return False
                await sleep(2)
                self._process.stdout.flush()


     def __get_progress_bar(self, percentage):
        progress = "{0}{1}\n**P:** {2}%".format(
            ''.join(['■' for i in range(floor(percentage / 10))]),
            ''.join(['□' for i in range(10 - floor(percentage / 10))]),
            round(percentage, 2))
        return progress
