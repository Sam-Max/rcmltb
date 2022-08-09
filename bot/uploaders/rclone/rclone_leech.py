from os import walk
import os
from re import search
from shutil import rmtree
from pyrogram.errors import FloodWait
from bot import DOWNLOAD_DIR, LOGGER, TG_SPLIT_SIZE, Bot, app
from bot.core.get_vars import get_val
from bot.utils.status_utils.extract_status import ExtractStatus
from bot.utils.status_utils.misc_utils import MirrorStatus, TelegramClient
from bot.utils.status_utils.rclone_status import RcloneStatus
from bot.uploaders.telegram.telegram_uploader import TelegramUploader
from bot.utils.bot_utils.misc_utils import get_rclone_config
from bot.utils.bot_utils.zip_utils import extract_archive, get_path_size, split_in_zip
from subprocess import Popen, PIPE
from asyncio import sleep
from bot.utils.status_utils.zip_status import ZipStatus

class RcloneLeech:
    def __init__(self, message, chat_id, origin_dir, dest_dir, file_name="", folder= False, isZip=False, extract=False, pswd=None, tag=None):
        self.__client = app if app is not None else Bot
        self.__user_msg = message
        self.id = self.__user_msg.id
        self.__file_name= file_name
        self.__is_Zip = isZip
        self.__extract = extract
        self.__chat_id = chat_id
        self.__origin_path = origin_dir
        self.__dest_path = dest_dir
        self.__folder= folder
        self.__total_files= 0
        self.__pswd = pswd
        self.tag = tag
        self.suproc = None
        self.__rclone_pr= None

    def clean(self, path):
        LOGGER.info(f"Cleaning Download: {path}")
        try:
            rmtree(path)
        except:
            os.remove(path)

    async def __onDownloadStart(self, origin_drive, conf_path):
        cmd = ['rclone', 'copy', f'--config={conf_path}', f'{origin_drive}:{self.__origin_path}', 
                          f'{self.__dest_path}', '-P']
        self.__rclone_pr = Popen(cmd, stdout=(PIPE),stderr=(PIPE))
        rclone_status= RcloneStatus(self.__rclone_pr, self.__user_msg, self.__file_name)
        status= await rclone_status.progress(MirrorStatus.STATUS_DOWNLOADING, TelegramClient.PYROGRAM)
        if status:
            await self.__onDownloadComplete()
        else:
            await self.__onDownloadCancel()      

    async def leech(self):
        origin_drive = get_val("DEFAULT_RCLONE_DRIVE")
        conf_path = get_rclone_config()
        await self.__user_msg.edit("Starting download...")
        await self.__onDownloadStart(origin_drive, conf_path)

    async def __onDownloadComplete(self):
            if self.__folder:
                f_path = self.__dest_path 
                f_name= f_path.split("/")[-2] + ".zip"   
                path = f'{DOWNLOAD_DIR}{f_name}'  
            else:
                f_path = os.path.join(self.__dest_path, self.__file_name)   
                f_name= self.__file_name  
                path = f_path + ".zip" 
            f_size = get_path_size(f_path) 
            if self.__is_Zip:
                LOGGER.info("Archiving...")  
                zip_sts= ZipStatus(f_name, f_size, self.__user_msg, self)
                await zip_sts.create_message()
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
                    self.__onDownloadError()
                    LOGGER.error('An error occurred while zipping!')
                if self.suproc.returncode == 0:
                    LOGGER.info('Process finished')
                    await upload(path, self.__user_msg, self.__chat_id) 
            elif self.__extract:
               LOGGER.info(f"Extracting...")
               ext_sts = ExtractStatus(f_name, f_size, self.__user_msg, self)
               await ext_sts.create_message()
               if os.path.isdir(self.__dest_path):
                    for dirpath, _, files in walk(self.__dest_path, topdown=False):
                        for file in files:
                            self.__total_files += 1   
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
                    await upload(self.__dest_path, self.__user_msg, self.__chat_id) 
               else:
                    path, msg= await extract_archive(path, password=self.pswd)
                    if path == False:
                        return await self.__client.send_message(self.__chat_id, msg)
                    await upload(path, self.__user_msg, self.__chat_id) 
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
                            path= await split_in_zip(f_path, size=TG_SPLIT_SIZE) 
                            await upload(path, self.__user_msg, self.__chat_id)
                        else:
                            await upload(f_path, self.__user_msg, self.__chat_id)
            await self.__user_msg.delete() 
            self.clean(self.__dest_path)
            msg = f'**Leech completed**\n'
            if self.__total_files > 0:
                msg += f'**Total Files:** {self.__total_files}'
            await self.__client.send_message(self.__chat_id, msg)  
    
            
    async def __onDownloadError(self):
        pass
 
    async def __onDownloadCancel(self):
        self.__rclone_pr.kill()
        await self.__user_msg.edit('Process cancelled!')  

async def upload(path, user_msg, chat_id):
    try:    
        tg_up= TelegramUploader(path, user_msg, chat_id)
        await tg_up.upload()
    except FloodWait as fw:
        await sleep(fw.seconds + 5)
        tg_up= TelegramUploader(path, user_msg, chat_id)
        await tg_up.upload()
    


        


           
