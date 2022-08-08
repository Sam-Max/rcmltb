from configparser import ConfigParser
from os import walk
import os
from re import search
from pyrogram.errors import FloodWait
from bot import DOWNLOAD_DIR, LOGGER, TG_SPLIT_SIZE, Bot, app, status_dict
from bot.core.get_vars import get_val
from bot.utils.status_utils.misc_utils import MirrorStatus, TelegramClient
from bot.utils.status_utils.rclone_status import RcloneStatus
from bot.uploaders.telegram.telegram_uploader import TelegramUploader
from bot.utils.bot_utils.misc_utils import clean,  get_rclone_config
from bot.utils.bot_utils.zip_utils import get_path_size, split_in_zip
from subprocess import Popen, PIPE
from asyncio import sleep
from bot.utils.status_utils.zip_status import ZipStatus


class RcloneLeech:
    def __init__(self, user_msg, chat_id, origin_dir, dest_dir, path= "", folder= False, is_Zip= False, extract= False, pswd=None) -> None:
        self.__client = app if app is not None else Bot
        self.__path= path
        self.__is_Zip =is_Zip
        self.__extract=extract
        self.__pswd = pswd
        self.__user_msg = user_msg
        self.id = self.__user_msg.id
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

        rclone_copy_cmd = ['rclone', 'copy', f'--config={conf_path}', f'{origin_drive}:{self.__origin_path}', 
                          f'{self.__dest_path}', '-P']
        self.__rclone_pr = Popen(rclone_copy_cmd, stdout=(PIPE),stderr=(PIPE))
        
        rclone_status= RcloneStatus(self.__rclone_pr, self.__user_msg, self.__path)
        
        status= await rclone_status.progress(
            status_type= MirrorStatus.STATUS_DOWNLOADING, 
            client_type= TelegramClient.PYROGRAM)

        if status== False:
            return      

        if self.__folder:
            if self.__is_Zip:
                LOGGER.info("Archiving...")  
                f_path = self.__dest_path
                f_size = get_path_size(f_path)
                f_name= f_path.split("/")[-2] + ".zip"
                path = f'{DOWNLOAD_DIR}{f_name}'
                zip_sts= ZipStatus(f_name, f_size, self.__user_msg, self)
                await zip_sts.create_message()
                status_dict[self.id]= zip_sts
                self.__total_files += 1 
                if self.__pswd is not None:
                    if int(f_size) > TG_SPLIT_SIZE:
                        LOGGER.info(f'Zip: orig_path: {f_path}, zip_path: {path}.0*')
                        self.suproc = Popen(["7z", f"-v{TG_SPLIT_SIZE}b", "a", "-mx=0", f"-p{self.pswd}", path, f_path])
                    else:
                        LOGGER.info(f'Zip: orig_path: {f_path}, zip_path: {path}')
                        self.suproc = Popen(["7z", "a", "-mx=0", f"-p{self.pswd}", path, f_path])
                elif int(f_size) > TG_SPLIT_SIZE:
                    LOGGER.info(f'Zip: orig_path: {f_path}, zip_path: {path}.0*')
                    self.suproc = Popen(["7z", f"-v{TG_SPLIT_SIZE}b", "a", "-mx=0", path, f_path])
                else:
                    LOGGER.info(f'Zip: orig_path: {f_path}, zip_path: {path}')
                    self.suproc = Popen(["7z", "a", "-mx=0", path, f_path])
                self.suproc.wait()
                if self.suproc.returncode == -9:
                    return
                elif self.suproc.returncode != 0:
                    LOGGER.error('An error occurred while zipping!')
                if self.suproc.returncode == 0:
                    LOGGER.info('Process finished')
                    try:
                        tg_up= TelegramUploader(path, self.__user_msg, self.__chat_id)
                        await tg_up.upload()
                    except FloodWait as fw:
                        await sleep(fw.seconds + 5)
                        tg_up= TelegramUploader(path, self.__user_msg, self.__chat_id)
                        await tg_up.upload()
                    await sleep(1)
                    del status_dict[self.id]
                    clean(path)
            elif self.__extract:
               LOGGER.info(f"Extracting...")
               if os.path.isdir(self.__dest_path):
                    for dirpath, subdir, files in walk(self.__dest_path, topdown=False):
                        for file in files:
                            if file.endswith((".zip", ".7z")) or search(r'\.part0*1\.rar$|\.7z\.0*1$|\.zip\.0*1$', file) \
                            or (file.endswith(".rar") and not search(r'\.part\d+\.rar$', file)):
                                f_path = os.path.join(dirpath, file)
                                if self.__pswd is not None:
                                    self.suproc = Popen(["7z", "x", f"-p{self.pswd}", f_path, f"-o{dirpath}", "-aot"])
                                else:
                                    self.suproc = Popen(["7z", "x", f_path, f"-o{dirpath}", "-aot"])
                                self.suproc.wait()
                                if self.suproc.returncode == -9:
                                    return
                                elif self.suproc.returncode != 0:
                                    LOGGER.error('Unable to extract archive splits!')
                        if self.suproc is not None and self.suproc.returncode == 0:
                            for file_ in files:
                                if file_.endswith((".rar", ".zip", ".7z")) or search(r'\.r\d+$|\.7z\.\d+$|\.z\d+$|\.zip\.\d+$', file_):
                                    del_path = os.path.join(dirpath, file_)
                                    os.remove(del_path)
                    for dirpath, subdir, files in walk(self.__dest_path, topdown=False):
                        for file in sorted(files):
                            self.__total_files += 1 
                            f_path = os.path.join(dirpath, file)
                            f_size = os.path.getsize(f_path)
                            if f_size == 0:
                                LOGGER.error(f"{f_size} size is zero, telegram don't upload zero size files")
                                continue
                            try:
                                tg_up= TelegramUploader(f_path, self.__user_msg, self.__chat_id)
                                await tg_up.upload()
                            except FloodWait as fw:
                                await sleep(fw.seconds + 5)
                                tg_up= TelegramUploader(f_path, self.__user_msg, self.__chat_id)
                                await tg_up.upload()
                            await sleep(1)
            else:
                for dirpath, _, files in walk(self.__dest_path):
                    for file in sorted(files):  
                        self.__total_files += 1    
                        f_path = os.path.join(dirpath, file)
                        f_size = os.path.getsize(f_path)
                        if f_size == 0:
                            LOGGER.error(f"{f_size} size is zero, telegram don't upload zero size files")
                            continue
                        if int(f_size) > TG_SPLIT_SIZE:
                            LOGGER.info(f"Splitting...")   
                            sp_dir= await split_in_zip(f_path, size=TG_SPLIT_SIZE) 
                            sp_list= os.listdir(sp_dir)
                            sp_list.sort() 
                            for file_ in sp_list :
                                f_path = os.path.join(sp_dir, file_)
                                try:
                                    tg_up= TelegramUploader(f_path,self.__user_msg, self.__chat_id)
                                    await tg_up.upload()
                                except FloodWait as fw:
                                    await sleep(fw.seconds + 5)
                                    tg_up= TelegramUploader(f_path, self.__user_msg, self.__chat_id)
                                    await tg_up.upload()
                                await sleep(1)
                        else:
                            try:
                                tg_up= TelegramUploader(f_path, self.__user_msg, self.__chat_id)
                                await tg_up.upload()
                            except FloodWait as fw:
                                await sleep(fw.seconds + 5)
                                tg_up= TelegramUploader(f_path, self.__user_msg, self.__chat_id)
                                await tg_up.upload()
                            await sleep(1)
            clean(self.__dest_path)
            msg= f'Leech completed.\nTotal Files: {self.__total_files}'
            await self.__client.send_message(self.__chat_id, msg)  
        else:
            f_path = os.path.join(self.__dest_path, self.__path)
            f_size = os.path.getsize(f_path)
            if self.__is_Zip:
                path = f_path + ".zip"     
                LOGGER.info("Zipping...")  
                if self.__pswd is not None:
                    if int(f_size) > TG_SPLIT_SIZE:
                        LOGGER.info(f'Zip: orig_path: {f_path}, zip_path: {path}.0*')
                        self.suproc = Popen(["7z", f"-v{TG_SPLIT_SIZE}b", "a", "-mx=0", f"-p{self.pswd}", path, f_path])
                    else:
                        LOGGER.info(f'Zip: orig_path: {f_path}, zip_path: {path}')
                        self.suproc = Popen(["7z", "a", "-mx=0", f"-p{self.pswd}", path, f_path])
                elif int(f_size) > TG_SPLIT_SIZE:
                    LOGGER.info(f'Zip: orig_path: {f_path}, zip_path: {path}.0*')
                    self.suproc = Popen(["7z", f"-v{TG_SPLIT_SIZE}b", "a", "-mx=0", path, f_path])
                else:
                    LOGGER.info(f'Zip: orig_path: {f_path}, zip_path: {path}')
                    self.suproc = Popen(["7z", "a", "-mx=0", path, f_path])
                self.suproc.wait()
                if self.suproc.returncode == -9:
                    return
                elif self.suproc.returncode != 0:
                    LOGGER.error('An error occurred while zipping!')
                if self.suproc.returncode == 0:
                    try:
                        tg_up= TelegramUploader(path, self.__user_msg, self.__chat_id)
                        await tg_up.upload()
                    except FloodWait as fw:
                        await sleep(fw.seconds + 5)
                        tg_up= TelegramUploader(path, self.__user_msg, self.__chat_id)
                        await tg_up.upload()
                    await sleep(1)
                    clean(path)
            elif self.__extract:
                LOGGER.info(f"Extracting...")
                dirpath= self.__dest_path
                if f_path.endswith((".zip", ".7z")) or search(r'\.part0*1\.rar$|\.7z\.0*1$|\.zip\.0*1$', f_path) \
                    or (f_path.endswith(".rar") and not search(r'\.part\d+\.rar$', f_path)):
                        if self.__pswd is not None:
                            self.suproc = Popen(["7z", "x", f"-p{self.pswd}", f_path, f"-o{dirpath}", "-aot"])
                        else:
                            self.suproc = Popen(["7z", "x", f_path, f"-o{dirpath}", "-aot"])
                        self.suproc.wait()
                        if self.suproc.returncode == -9:
                            return
                        elif self.suproc.returncode != 0:
                            LOGGER.error('Unable to extract archive splits!')
                if self.suproc is not None and self.suproc.returncode == 0:
                    if f_path.endswith((".rar", ".zip", ".7z")) or search(r'\.r\d+$|\.7z\.\d+$|\.z\d+$|\.zip\.\d+$', f_path):
                        del_path = f_path
                        os.remove(del_path)
                for dirpath, subdir, files in walk(dirpath, topdown=False):
                        for file in sorted(files):
                            self.__total_files += 1 
                            f_path = os.path.join(dirpath, file)
                            f_size = os.path.getsize(f_path)
                            if f_size == 0:
                                LOGGER.error(f"{f_size} size is zero, telegram don't upload zero size files")
                                continue
                            try:
                                tg_up= TelegramUploader(f_path, self.__user_msg, self.__chat_id)
                                await tg_up.upload()
                            except FloodWait as fw:
                                await sleep(fw.seconds + 5)
                                tg_up= TelegramUploader(f_path, self.__user_msg, self.__chat_id)
                                await tg_up.upload()
                            await sleep(1)
            else:
                if int(f_size) > TG_SPLIT_SIZE:
                    LOGGER.info(f"Splitting...")     
                    sp_dir= await split_in_zip(f_path, size=TG_SPLIT_SIZE) 
                    sp_list= os.listdir(sp_dir)
                    sp_list.sort() 
                    for file in sp_list :
                        f_path = os.path.join(sp_list, file)
                        try:
                            tg_up= TelegramUploader(f_path, self.__user_msg, self.__chat_id)
                            await tg_up.upload()
                        except FloodWait as fw:
                            await sleep(fw.seconds + 5)
                            tg_up= TelegramUploader(f_path, self.__user_msg, self.__chat_id)
                            await tg_up.upload()
                        await sleep(1)
                else:
                    try:    
                        tg_up= TelegramUploader(f_path, self.__user_msg, self.__chat_id)
                        await tg_up.upload()
                    except FloodWait as fw:
                        await sleep(fw.seconds + 5)
                        tg_up= TelegramUploader(f_path, self.__user_msg, self.__chat_id)
                        await tg_up.upload()
            clean(self.__dest_path)   
