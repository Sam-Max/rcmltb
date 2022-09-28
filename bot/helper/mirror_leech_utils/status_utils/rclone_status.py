from asyncio import sleep
from math import floor
import re
import time
from bot import EDIT_SLEEP_SECS, status_dict, status_dict_lock
from bot.helper.ext_utils.message_utils import editMessage
from bot.helper.ext_utils.misc_utils import ButtonMaker
from bot.helper.mirror_leech_utils.status_utils.status_utils import MirrorStatus, get_bottom_status



class RcloneStatus:
    def __init__(self, process, message, status_type, gid, name=""):
        self._rc_process = process
        self.message = message
        self._id = self.message.id
        self._gid= gid
        self._name= name
        self._status_type= status_type
        self._status_msg_text= ""
        self.is_cancelled = False

    async def start(self):
        async with status_dict_lock:
            status_dict[self._id] = self
        blank = 0
        sleeps = False
        start = time.time()
        button= ButtonMaker()
        button.cb_buildbutton('Cancel', data=f"cancel {self._gid}")
        status= self.status()
        self._status_msg_text= await self.__create_empty_status(status, self._name)
        await editMessage(self._status_msg_text, self.message, reply_markup=button.build_menu(1))
        
        while True:
            data = await self._rc_process.stdout.readline()
            data = data.decode().strip()
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
                    self._status_msg_text= self.get_status_message(status, prg, self._name, nstr)
                    await editMessage(self._status_msg_text, self.message, reply_markup=button.build_menu(1))

            if data == '':
                blank += 1
                if blank == 20:
                    return True
            else:
                blank = 0

            if sleeps:
                sleeps = False
                if self.is_cancelled:
                    async with status_dict_lock:
                        del status_dict[self._id] 
                    self._rc_process.kill()
                    return False
                await sleep(2)

    def get_status_msg(self):
        return self._status_msg_text

    def name(self):
        return self._name

    def status(self):
        if self._status_type == MirrorStatus.STATUS_UPLOADING:
            return MirrorStatus.STATUS_UPLOADING
        elif self._status_type == MirrorStatus.STATUS_CLONING:
            return MirrorStatus.STATUS_CLONING
        elif self._status_type == MirrorStatus.STATUS_COPYING:
            return MirrorStatus.STATUS_COPYING
        else:
            return MirrorStatus.STATUS_DOWNLOADING

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

    async def __create_empty_status(self, status_type, name):
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
        return status_msg

    def __get_progress_bar(self, percentage):
        return "{0}{1}\n**P:** {2}%".format(
        ''.join(['■' for i in range(floor(percentage / 10))]),
        ''.join(['□' for i in range(10 - floor(percentage / 10))]),
        round(percentage, 2))

    def gid(self):
        return self._gid

    def cancel_download(self):
        self.is_cancelled = True
