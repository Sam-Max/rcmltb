from configparser import ConfigParser
from os import walk
import os
from re import search
import time
from pyrogram.errors import FloodWait
from subprocess import run
from bot import DOWNLOAD_DIR, LOGGER, TG_SPLIT_SIZE, Bot, app
from bot.core.get_vars import get_val
from bot.utils.bot_utils.exceptions import NotSupportedExtractionArchive
from bot.utils.status_utils.misc_utils import MirrorStatus
from bot.utils.status_utils.rclone_status import RcloneStatus
from bot.uploaders.telegram.telegram_uploader import TelegramUploader
from bot.utils.bot_utils.misc_utils import check_extract_format, clean_filepath, clean_path, get_rclone_config, get_readable_size
from bot.utils.bot_utils.zip_utils import extract_archive, split_in_zip
from subprocess import Popen, PIPE
from asyncio import sleep


class RcloneLeech:
    def __init__(self, user_msg, chat_id, origin_dir, dest_dir, folder= False, path= "", is_Zip= False, extract= False, pswd=None) -> None:
        self.__client = app if app is not None else Bot
        self.__path= path
        self.__is_Zip =is_Zip
        self.__extract=extract
        self.__pswd = pswd
        self.__user_msg = user_msg
        self.__chat_id = chat_id
        self.__origin_path = origin_dir
        self.__dest_path = dest_dir
        self.__folder= folder
        self.__total_files= 0
        self.suproc= None

    async def leech(self):
        await self.__user_msg.edit("Starting download...")
        origin_drive = get_val("DEFAULT_RCLONE_DRIVE")
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

        rclone_copy_cmd = ['rclone', 'copy', f'--config={conf_path}', f'{origin_drive}:{self.__origin_path}', f'{self.__dest_path}', '-P']
        self.__rclone_pr = Popen(rclone_copy_cmd, stdout=(PIPE),stderr=(PIPE))
        
        rclone_status= RcloneStatus(self.__rclone_pr, self.__user_msg, self.__path)
        status= await rclone_status.progress(
            status_type= MirrorStatus.STATUS_DOWNLOADING, 
            client_type='pyrogram')
        if status== False:
            return      

        if self.__folder:
            for root, _, files in walk(self.__dest_path):
                if len(files) == 0:
                    continue 
                for file in sorted(files):  
                    self.__total_files += 1    
                    f_path = os.path.join(root, file)
                    f_size = os.path.getsize(f_path)
                    if f_size == 0:
                        LOGGER.error(f"{f_size} size is zero, telegram don't upload zero size files")
                        continue
                    if int(f_size) > TG_SPLIT_SIZE:
                        message= await self.__client.send_message(self.__chat_id, f"Splitting...")     
                        split_dir= await split_in_zip(f_path, size=TG_SPLIT_SIZE) 
                        dir_list= os.listdir(split_dir)
                        dir_list.sort() 
                        for file_ in dir_list :
                            f_path = os.path.join(split_dir, file_)
                            try:
                                tg_up= TelegramUploader(f_path, message, self.__chat_id)
                                await tg_up.upload()
                            except FloodWait as fw:
                                await sleep(fw.seconds + 5)
                                tg_up= TelegramUploader(f_path, message, self.__chat_id)
                                await tg_up.upload()
                            await sleep(1)
                    else:
                        if self.__is_Zip:
                            pass
                        if self.__extract:
                           if os.path.isdir(self.__dest_path):
                                if file.endswith((".zip", ".7z")) or search(r'\.part0*1\.rar$|\.7z\.0*1$|\.zip\.0*1$', file) \
                                or (file.endswith(".rar") and not search(r'\.part\d+\.rar$', file)):
                                    if self.__pswd is not None:
                                        self.suproc = Popen(["7z", "x", f"-p{self.pswd}", f_path, f"-o{root}", "-aot"])
                                    else:
                                        self.suproc = Popen(["7z", "x", f_path, f"-o{root}", "-aot"])
                                    self.suproc.wait()
                                    if self.suproc.returncode == -9:
                                        return
                                    elif self.suproc.returncode != 0:
                                        LOGGER.error('Unable to extract archive splits!')
                                if self.suproc is not None and self.suproc.returncode == 0:
                                    if file.endswith((".rar", ".zip", ".7z")) or search(r'\.r\d+$|\.7z\.\d+$|\.z\d+$|\.zip\.\d+$', file):
                                        del_path = os.path.join(root, file)
                                        os.remove(del_path)
                        if os.path.exists(f_path):
                            try:
                                tg_up= TelegramUploader(f_path, self.__user_msg, self.__chat_id)
                                await tg_up.upload()
                            except FloodWait as fw:
                                await sleep(fw.seconds + 5)
                                tg_up= TelegramUploader(f_path, self.__user_msg, self.__chat_id)
                                await tg_up.upload()
                            await sleep(1)
                clean_path(self.__dest_path)
                msg= f'Leech completed!\nTotal: {self.__total_files}'
                await self.__client.send_message(self.__chat_id, msg)  
        else:
            f_path = os.path.join(self.__dest_path, self.__path)
            f_size = os.path.getsize(f_path)
            if int(f_size) > TG_SPLIT_SIZE:
                message= await self.__client.send_message(self.__chat_id, f"Splitting...")     
                split_dir= await split_in_zip(f_path, size=TG_SPLIT_SIZE) 
                os.remove(f_path) 
                dir_list= os.listdir(split_dir)
                dir_list.sort() 
                for file in dir_list :
                    f_path = os.path.join(split_dir, file)
                    try:
                        tg_up= TelegramUploader(f_path, message, self.__chat_id)
                        await tg_up.upload()
                    except FloodWait as fw:
                        await sleep(fw.seconds + 5)
                        tg_up= TelegramUploader(f_path, message, self.__chat_id)
                        await tg_up.upload()
                    await sleep(1)
                await self.__client.send_message(self.__chat_id, "Nothing else to upload!")
            else:
                if self.__is_Zip:
                    try:
                        base = os.path.basename(f_path)
                        file_name = base.rsplit('.', maxsplit=1)[0]
                        file_name = file_name + ".zip"
                        path = f'{DOWNLOAD_DIR}{self.__dest_path}/{file_name}'
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
                            check_extract_format(f_path)
                            LOGGER.info("Extracting...")
                        else:
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
                    tg_up= TelegramUploader(path, self.__user_msg, self.__chat_id)
                    await tg_up.upload()
                except FloodWait as fw:
                    await sleep(fw.seconds + 5)
                    tg_up= TelegramUploader(path, message, self.__chat_id)
                    await tg_up.upload()
                clean_filepath(path)   
