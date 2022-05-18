import asyncio
from random import randrange
import re
import subprocess
import logging
import time
from bot.core.get_vars import get_val
from bot.utils.get_rclone_conf import get_config
from telethon import Button

log = logging.getLogger(__name__)

class RcloneCopy:
    def __init__(self, user_msg) -> None:
        self.id = self.__create_id(8)
        self.__user_msg = user_msg
        self.cancel = False

    def __create_id(self, count):
        map = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        id = ''
        i = 0
        while i < count:
            rnd = randrange(len(map))
            id += map[rnd]
            i += 1
        return id

    async def copy(self):
        origin_drive = get_val("ORIGIN_DRIVE")
        origin_dir = get_val("ORIGIN_DIR")
        dest_drive = get_val("DEST_DRIVE")
        dest_dir = get_val("DEST_DIR")

        conf_path = await get_config()

        rclone_copy_cmd = ['rclone', 'copy', f'--config={conf_path}', f'{origin_drive}:{origin_dir}',
                       f'{dest_drive}:{dest_dir}', '-P']

        await self.__user_msg.edit(text="Preparing to copy...")

        self.__rclone_pr = subprocess.Popen(
            rclone_copy_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        rcres = await self.__rclone_update()

        if rcres == False:
            self.__rclone_pr.kill()
            await self.__user_msg.edit("Copy cancelled")
            return

        await self.__user_msg.edit("Copied Successfully ✅")

    async def __rclone_update(self):
        blank = 0
        process = self.__rclone_pr
        user_message = self.__user_msg
        sleeps = False
        start = time.time()
        edit_time= get_val("EDIT_SLEEP_SECS")
        msg = ""
        msg1 = ""

        while True:
            data = process.stdout.readline().decode().strip()
            mat = re.findall("Transferred:.*ETA.*", data)

            if mat is not None:
                if len(mat) > 0:
                    sleeps = True
                    nstr = mat[0].replace("Transferred:", "")
                    nstr = nstr.strip()
                    nstr = nstr.split(",")
                    percent = nstr[1].strip("% ")
                    try:
                        percent = int(percent)
                    except:
                        percent = 0
                    prg = self.__progress_bar(percent)

                    msg = '**Copying...\n{} \n{} \nSpeed:- {} \nETA:- {}\n**'.format(nstr[0], prg, nstr[2], nstr[3].replace("ETA", ""))
                    
                    if time.time() - start > edit_time:
                        if msg1 != msg:
                            start = time.time()
                            await user_message.edit(text=msg, buttons= [[Button.inline("Cancel", f"upcancel_{self.id}".encode('UTF-8'))]])
                            msg1= msg

            if data == "":
                blank += 1
                if blank == 20:
                    break
            else:
                blank = 0

            if sleeps:
                sleeps = False
                if self.cancel:
                    return False
                await asyncio.sleep(2)
                process.stdout.flush()       

    def __progress_bar(self, percentage):
        comp ="▪️"
        ncomp ="▫️"
        pr = ""

        try:
            percentage=int(percentage)
        except:
            percentage = 0

        for i in range(1, 11):
            if i <= int(percentage/10):
                pr += comp
            else:
                pr += ncomp
        return pr


