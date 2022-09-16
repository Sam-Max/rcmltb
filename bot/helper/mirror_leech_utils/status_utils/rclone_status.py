from asyncio import sleep
from math import floor
from os.path import basename
import re
import time
from bot import EDIT_SLEEP_SECS, status_dict, status_dict_lock
from bot.helper.ext_utils.message_utils import editMessage
from bot.helper.ext_utils.misc_utils import ButtonMaker
from bot.helper.mirror_leech_utils.status_utils.status_utils import MirrorStatus, get_bottom_status



class RcloneStatus:
    def __init__(self, process, message, name=""):
        self._process = process
        self._message = message
        self.id = self._message.id
        self._name= name
        self._status_msg= ""
        self.is_cancelled = False

    def get_status_msg(self):
        return self._status_msg     

    async def start(self, status_type):
        async with status_dict_lock:
            status_dict[self.id] = self
        blank = 0
        sleeps = False
        start = time.time()
        button= ButtonMaker()
        button.cb_buildbutton('Cancel', data=f"cancel_rclone_{self.id}")
        await self.__create_empty_status(status_type, self._name, button)
        
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

                if time.time() - start > EDIT_SLEEP_SECS:
                    start = time.time()
                    self._status_msg= self.get_status_message(status_type, prg, self._name, nstr)
                    await editMessage(self._status_msg, self._message, reply_markup=button.build_menu(1))

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
                if self.is_cancelled:
                    async with status_dict_lock:
                        del status_dict[self.id] 
                    self._process.kill()
                    return False
                await sleep(2)
                self._process.stdout.flush()

    def get_status_message(self, status_type, prg, name, nstr):
        if status_type == MirrorStatus.STATUS_UPLOADING:
            status_msg = '**Name:** `{}`\n**Status:** {}\n{}\n**Uploaded:** {}\n**Speed:** {} | **ETA:** {}\n'.format(
                        name, status_type, prg, nstr[0], nstr[2], nstr[3].replace('ETA', ''))
        elif status_type == MirrorStatus.STATUS_CLONING:
            status_msg = '**Name:** `{}`\n**Status:** {}\n{}\n**Downloaded:** {}\n**Speed:** {} | **ETA:** {}\n'.format(
                                name, status_type, prg, nstr[0], nstr[2], nstr[3].replace('ETA', ''))
        elif status_type == MirrorStatus.STATUS_DOWNLOADING:
            status_msg = '**Name:** `{}`\n**Status:** {}\n{}\n**Downloaded:** {}\n**Speed:** {} | **ETA:** {}\n'.format(
                                name, status_type, prg, nstr[0], nstr[2], nstr[3].replace('ETA', ''))
        elif status_type == MirrorStatus.STATUS_COPYING:
            status_msg = '**Status:** {}\n{}\n**Copied:** {}\n**Speed:** {} | **ETA:** {}\n'.format(
                                    status_type, prg, nstr[0], nstr[2], nstr[3].replace('ETA', ''))
        status_msg += get_bottom_status()   
        return status_msg

    async def __create_empty_status(self, status_type, name, button):
        prg = self.__get_progress_bar(0)
        if status_type == MirrorStatus.STATUS_UPLOADING:
            status_msg = '**Name:** `{}`\n**Status:** {}\n{}\n**Uploaded:** {}\n**Speed:** {} | **ETA:** {}\n'.format(
                        name, status_type, prg, "0 B", "0 B/s ", "-")
        elif status_type == MirrorStatus.STATUS_CLONING:
            status_msg = '**Name:** `{}`\n**Status:** {}\n{}\n**Downloaded:** {}\n**Speed:** {} | **ETA:** {}\n'.format(
                                name, status_type, prg, "0 B", "0 B/s ", "-")
        elif status_type == MirrorStatus.STATUS_DOWNLOADING:
            status_msg = '**Name:** `{}`\n**Status:** {}\n{}\n**Downloaded:** {}\n**Speed:** {} | **ETA:** {}\n'.format(
                                name, status_type, prg, "0 B", "0 B/s ", "-")
        elif status_type == MirrorStatus.STATUS_COPYING:
            status_msg = '**Status:** {}\n{}\n**Copied:** {}\n**Speed:** {} | **ETA:** {}\n'.format(
                                    status_type, prg, "0 B", "0 B/s ", "-")
        status_msg += get_bottom_status()  
        await editMessage(status_msg, self._message, button.build_menu(1)) 

    def __get_progress_bar(self, percentage):
        return "{0}{1}\n**P:** {2}%".format(
        ''.join(['■' for i in range(floor(percentage / 10))]),
        ''.join(['□' for i in range(10 - floor(percentage / 10))]),
        round(percentage, 2))
