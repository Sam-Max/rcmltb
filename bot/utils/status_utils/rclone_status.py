import asyncio
import math
from os.path import basename
from random import randrange
import re
import time
from pyrogram.errors.exceptions import FloodWait
from telethon.errors import FloodWaitError
from bot import EDIT_SLEEP_SECS, GLOBAL_RCLONE, LOGGER
from bot.utils.status_utils.misc_utils import MirrorStatus, get_bottom_status
from telethon import Button
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

class RcloneStatus:
     def __init__(self, process, user_message, path=''):
        self._process = process
        self.id = self.__create_id(8)
        self._path= path
        self._user_message = user_message
        self.cancelled = False

     def __create_id(self, count):
        map = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        id = ''
        i = 0
        while i < count:
            rnd = randrange(len(map))
            id += map[rnd]
            i += 1
        return id

     async def progress(self, status_type, client_type):
        GLOBAL_RCLONE.add(self)
        LOGGER.info(status_type)
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
                    msg = '**Name:** `{}`\n**Status:** {}\n{}\n**Uploaded:** {}\n**Speed:** {} | **ETA:** {}\n'.format(
                              basename(self._path), status_type, prg, nstr[0], nstr[2], nstr[3].replace('ETA', ''))
                if status_type == MirrorStatus.STATUS_DOWNLOADING:
                    msg = '**Name:** `{}`\n**Status:** {}\n{}\n**Downloaded:** {}\n**Speed:** {} | **ETA:** {}\n'.format(
                                        basename(self._path), status_type, prg, nstr[0], nstr[2], nstr[3].replace('ETA', ''))
                if status_type == MirrorStatus.STATUS_COPYING:
                    msg = '**Status:** {}\n{}\n**Copied:** {}\n**Speed:** {} | **ETA:** {}\n'.format(
                                            status_type, prg, nstr[0], nstr[2], nstr[3].replace('ETA', ''))
                msg += get_bottom_status()
                
                if time.time() - start > EDIT_SLEEP_SECS:
                        start = time.time()
                        if client_type == 'pyrogram':
                              try:
                                   await self._user_message.edit(text=msg, reply_markup=(InlineKeyboardMarkup([
                                   [InlineKeyboardButton('Cancel', callback_data=(
                                        f"cancel_rclone_{self.id}".encode('UTF-8')))]
                                   ])))
                              except FloodWait as fw:
                                    LOGGER.warning(f"FloodWait : Sleeping {fw.value}s")
                                    await asyncio.sleep(fw.value)
                              except:
                                   pass
                        if client_type == 'telethon':
                              try:
                                   await self._user_message.edit(text=msg, 
                                   buttons= [[Button.inline("Cancel", f"cancel_rclone_{self.id}".encode('UTF-8'))]])
                              except FloodWaitError as fw:
                                   LOGGER.warning(f"FloodWait : Sleeping {fw.seconds}s")
                                   await asyncio.sleep(fw.value)
                              except:
                                   pass 
            if data == '':
                blank += 1
                if blank == 20:
                    GLOBAL_RCLONE.remove(self)     
                    break
            else:
                blank = 0

            if sleeps:
                sleeps = False
                if self.cancelled:
                    self._process.kill()
                    await self._user_message.edit('Process cancelled!.')  
                    GLOBAL_RCLONE.remove(self)   
                    return False
                await asyncio.sleep(2)
                self._process.stdout.flush()


     def __get_progress_bar(self, percentage):
        progress = "{0}{1}\n**P:** {2}%".format(
            ''.join(['■' for i in range(math.floor(percentage / 10))]),
            ''.join(['□' for i in range(10 - math.floor(percentage / 10))]),
            round(percentage, 2))
        return progress
