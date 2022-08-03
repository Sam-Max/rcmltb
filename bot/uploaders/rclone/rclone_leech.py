from configparser import ConfigParser
from os import walk
import os
import time
from pyrogram.errors import FloodWait
from subprocess import run
from bot import LOGGER, TG_SPLIT_SIZE, Bot, app
from bot.core.get_vars import get_val
from bot.utils.bot_utils.exceptions import NotSupportedExtractionArchive
from bot.utils.status_utils.misc_utils import MirrorStatus
from bot.utils.status_utils.rclone_status import RcloneStatus
from bot.uploaders.telegram.telegram_uploader import TelegramUploader
from bot.utils.bot_utils.misc_utils import check_format_for_extraction, clean_filepath, clean_path, get_rclone_config, get_readable_size
from bot.utils.bot_utils.zip_utils import extract_archive, split_in_zip
from subprocess import Popen, PIPE
import asyncio



class RcloneLeech:
    def __init__(self, user_msg, chat_id, origin_dir, dest_dir, folder= False, path= "", is_Zip= False, extract= False, pswd=None) -> None:
        self.__client = app if app is not None else Bot
        self.__path= path
        self.__is_Zip =is_Zip
        self.__extract=extract
        self.__pswd = pswd
        self.__user_msg = user_msg
        self.__chat_id = chat_id
        self.__origin_dir = origin_dir
        self.__dest_dir = dest_dir
        self.__folder= folder

    async def leech(self):
        await self.__user_msg.edit("Starting download...")
        origin_drive = get_val("DEFAULT_RCLONE_DRIVE")
        tg_split_size= get_readable_size(TG_SPLIT_SIZE) 
        conf_path = get_rclone_config()
        conf = ConfigParser()
        conf.read(conf_path)
        drive_name = ""

        for i in conf.sections():
            if origin_drive == str(i):
                if conf[i]["type"] == "drive":
                    LOGGER.info("G-Drive Download Detected.")
                else:
                    drive_name = conf[i]["type"]
                    LOGGER.info(f"{drive_name} Download Detected.")
                break

        rclone_copy_cmd = ['rclone', 'copy', f'--config={conf_path}', f'{origin_drive}:{self.__origin_dir}', f'{self.__dest_dir}', '-P']
        self.__rclone_pr = Popen(rclone_copy_cmd, stdout=(PIPE),stderr=(PIPE))
        rclone_status= RcloneStatus(self.__rclone_pr, self.__user_msg, self.__path)
        status= await rclone_status.progress(status_type= MirrorStatus.STATUS_DOWNLOADING, client_type='pyrogram')
        if status== False:return      

        if self.__folder:
            for root, _, files in walk(self.__dest_dir):
                if len(files) == 0:continue 
                for i, file in enumerate(sorted(files)):  
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
                    f_path = os.path.join(root, file)
                    f_size = os.path.getsize(f_path)
                    if int(f_size) > TG_SPLIT_SIZE:
                        message= await self.__client.send_message(self.__chat_id, f"File larger than {tg_split_size}, Splitting...")     
                        split_dir= await split_in_zip(f_path, size=TG_SPLIT_SIZE) 
                        clean_filepath(f_path)
                        dir_list= os.listdir(split_dir)
                        dir_list.sort() 
                        for file in dir_list :
                            f_path = os.path.join(split_dir, file)
                            try:
                                await TelegramUploader(f_path, message, self.__chat_id).upload()
                            except FloodWait as fw:
                                await asyncio.sleep(fw.seconds + 5)
                                await TelegramUploader(f_path, message, self.__chat_id).upload()
                            time.sleep(timer)
                    else:
                        try:
                            await TelegramUploader(f_path, self.__user_msg, self.__chat_id).upload()
                        except FloodWait as fw:
                            await asyncio.sleep(fw.seconds + 5)
                            await TelegramUploader(f_path, self.__user_msg, self.__chat_id).upload()
                        time.sleep(timer)
            clean_path(self.__dest_dir)
            await self.__client.send_message(self.__chat_id, "Nothing else to upload!")  
        else:
            f_path = os.path.join(self.__dest_dir, self.__path)
            f_size = os.path.getsize(f_path)
            if int(f_size) > TG_SPLIT_SIZE:
                message= await self.__client.send_message(self.__chat_id, f"File larger than {tg_split_size}, Splitting...")     
                split_dir= await split_in_zip(f_path, size=TG_SPLIT_SIZE) 
                os.remove(f_path) 
                dir_list= os.listdir(split_dir)
                dir_list.sort() 
                for file in dir_list :
                    timer = 5
                    f_path = os.path.join(split_dir, file)
                    try:
                        await TelegramUploader(f_path, message, self.__chat_id).upload()
                    except FloodWait as fw:
                        await asyncio.sleep(fw.seconds + 5)
                        await TelegramUploader(f_path, message, self.__chat_id).upload()
                    time.sleep(timer)
                await self.__client.send_message(self.__chat_id, "Nothing else to upload!")
            else:
                if self.__is_Zip:
                    try:
                        base = os.path.basename(f_path)
                        file_name = base.rsplit('.', maxsplit=1)[0]
                        path = os.path.join(os.getcwd(), "Downloads", self.__dest_dir, file_name + ".zip")
                        size = os.path.getsize(f_path)
                        if self.__pswd is not None:
                            if int(size) > TG_SPLIT_SIZE:
                                run(["7z", f"-v{TG_SPLIT_SIZE}b", "a", "-mx=0", f"-p{self.__pswd}", path, f_path])     
                            else:
                                run(["7z", "a", "-mx=0", f"-p{self.__pswd}", path, f_path])
                        elif int(size) > TG_SPLIT_SIZE:
                            run(["7z", f"-v{TG_SPLIT_SIZE}b", "a", "-mx=0", path, f_path])
                        else:
                            run(["7z", "a", "-mx=0", path, f_path])
                    except FileNotFoundError:
                        LOGGER.info('File to archive not found!')
                        return
                elif self.__extract:
                    try:
                        if os.path.isfile(f_path):
                            check_format_for_extraction(f_path)
                            LOGGER.info("Extracting...")
                        ex_path= await extract_archive(f_path, self.__pswd)
                        if ex_path is False:
                            LOGGER.info('Unable to extract archive!')
                        else:
                            files= os.listdir(ex_path)     
                            for file in files:  
                                path = os.path.join(ex_path, file)
                    except NotSupportedExtractionArchive:
                        LOGGER.info("Not any valid archive.")
                        return 
                else:
                    path= f_path
                try:    
                    await TelegramUploader(path, self.__user_msg, self.__chat_id).upload()
                except FloodWait as fw:
                    await asyncio.sleep(fw.seconds + 5)
                    await TelegramUploader(path, message, self.__chat_id).upload()
                clean_filepath(path)   
