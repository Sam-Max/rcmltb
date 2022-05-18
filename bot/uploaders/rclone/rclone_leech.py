from configparser import ConfigParser
from os import walk
import os
from random import randrange
import re
import time
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.core.get_vars import get_val
from bot.uploaders.telegram.telegram_upload import upload_media_pyro
from bot.utils.get_size_p import get_size
from bot.utils.misc_utils import clear_stuff
from bot.utils.zip_utils import split_in_zip
from bot.utils.get_rclone_conf import get_config
import logging
import subprocess
import asyncio

log = logging.getLogger(__name__)

class RcloneLeech:
    def __init__(self, client, user_msg, chat_id, origin_dir, dest_dir, folder= False, path= "") -> None:
        self.id = self.__create_id(8)
        self.__client = client
        self.__user_msg = user_msg
        self.__chat_id = chat_id
        self.__origin_dir = origin_dir
        self.cancel = False
        self.__folder= folder
        self.__path= path
        self.__dest_dir = dest_dir

    def __create_id(self, count):
        map = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        id = ''
        i = 0
        while i < count:
            rnd = randrange(len(map))
            id += map[rnd]
            i += 1
        return id

    async def leech(self):
        await self.__user_msg.edit("Preparing for download...")
        origin_drive = get_val("DEF_RCLONE_DRIVE")
        tg_split_size= get_size(get_val("TG_SPLIT_SIZE")) 
        conf_path = await get_config()
        conf = ConfigParser()
        conf.read(conf_path)
        drive_name = ""

        for i in conf.sections():
            if origin_drive == str(i):
                if conf[i]["type"] == "drive":
                    log.info("Google Drive Download Detected.")
                else:
                    drive_name = conf[i]["type"]
                    log.info(f"{drive_name} Download Detected.")
                break

        rclone_copy_cmd = [
            'rclone', 'copy', f'--config={conf_path}', f'{origin_drive}:{self.__origin_dir}', f'{self.__dest_dir}', '-P']

        self.__rclone_pr = subprocess.Popen(
            rclone_copy_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        rcres= await self.__rclone_update()

        if rcres == False:
            self.__rclone_pr.kill()
            await self.__user_msg.edit("Leech cancelled")
            return 

        if self.__folder:
            for dirpath, _, filenames in walk(self.__dest_dir):
                if len(filenames) == 0:continue 
                sorted_fn= sorted(filenames)
                for i, file in enumerate(sorted_fn):  
                    timer = 60  
                    if i < 25:
                        timer = 5
                    if i < 50 and i > 25:
                        timer = 10
                    if i < 100 and i > 50:
                        timer = 15
                    if i < 150 and i > 100:
                        timer = 20
                    if i < 200 and i > 150:
                        timer = 25
                    f_path = os.path.join(dirpath, file)
                    f_size = os.path.getsize(f_path)
                    if int(f_size) > get_val("TG_SPLIT_SIZE"):
                        message= await self.__client.send_message(self.__chat_id, f"File larger than {tg_split_size}, Splitting...")     
                        split_dir= await split_in_zip(f_path, size=get_val("TG_SPLIT_SIZE")) 
                        os.remove(f_path) 
                        dir_list= os.listdir(split_dir)
                        dir_list.sort() 
                        for file in dir_list :
                            f_path = os.path.join(split_dir, file)
                            try:
                                await upload_media_pyro(self.__client, message, self.__chat_id, f_path)
                            except FloodWait as fw:
                                await asyncio.sleep(fw.seconds + 5)
                                await upload_media_pyro(self.__client, message, self.__chat_id, f_path)     
                            time.sleep(timer)
                    else:
                        try:
                            await upload_media_pyro(self.__client, self.__user_msg, self.__chat_id, f_path)
                        except FloodWait as fw:
                            await asyncio.sleep(fw.seconds + 5)
                            await upload_media_pyro(self.__client, self.__user_msg, self.__chat_id, f_path)
                        time.sleep(timer)
            await clear_stuff("./Downloads")
            await self.__client.send_message(self.__chat_id, "Nothing else to upload!")  
        else:
            f_path = os.path.join(self.__dest_dir, self.__path)
            f_size = os.path.getsize(f_path)
            if int(f_size) > get_val("TG_SPLIT_SIZE"):
                message= await self.__client.send_message(self.__chat_id, f"File larger than {tg_split_size}, Splitting...")     
                split_dir= await split_in_zip(f_path, size=get_val("TG_SPLIT_SIZE")) 
                os.remove(f_path) 
                dir_list= os.listdir(split_dir)
                dir_list.sort() 
                for file in dir_list :
                    timer = 5
                    f_path = os.path.join(split_dir, file)
                    try:
                        await upload_media_pyro(self.__client, message, self.__chat_id, f_path)
                    except FloodWait as fw:
                        await asyncio.sleep(fw.seconds + 5)
                        await upload_media_pyro(self.__client, message, self.__chat_id, f_path)
                    time.sleep(timer)
                await clear_stuff("./Downloads")    
                await self.__client.send_message(self.__chat_id, "Nothing else to upload!")
            else:
                try:    
                    await upload_media_pyro(self.__client, self.__user_msg, self.__chat_id, f_path)
                except FloodWait as fw:
                    await asyncio.sleep(fw.seconds + 5)
                    await upload_media_pyro(self.__client, self.__user_msg, self.__chat_id, f_path)   

    async def __rclone_update(self):
        blank = 0
        process = self.__rclone_pr
        user_message = self.__user_msg
        sleeps = False
        start = time.time()
        edit_time = get_val('EDIT_SLEEP_SECS')
        msg = ''
        msg1 = ''
        while True:
            data = process.stdout.readline().decode()
            data = data.strip()
            mat = re.findall('Transferred:.*ETA.*', data)
            
            if mat is not None and len(mat) > 0:
                sleeps = True
                nstr = mat[0].replace('Transferred:', '')
                nstr = nstr.strip()
                nstr = nstr.split(',')
                percent = nstr[1].strip('% ')
                try:
                    percent = int(percent)
                except:
                    percent = 0
                prg = self.__progress_bar(percent)
                
                msg = '<b>{}...\n{} \n{} \nSpeed:- {} \nETA:- {}\n</b>'.format('Downloading...', nstr[0], prg, nstr[2], nstr[3].replace('ETA', ''))
                
                if time.time() - start > edit_time:
                    if msg1 != msg:
                        start = time.time()
                        await user_message.edit(text=msg, reply_markup=(InlineKeyboardMarkup([
                            [InlineKeyboardButton('Cancel', callback_data=(f"upcancel_{self.id}".encode('UTF-8')))]
                            ])))                            
                        msg1 = msg
                
            if data == '':
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