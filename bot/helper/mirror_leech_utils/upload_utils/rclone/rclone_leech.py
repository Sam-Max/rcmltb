from os import path as ospath, remove, walk
from re import search
from pyrogram.errors import FloodWait
from bot import LOGGER, TG_SPLIT_SIZE
from subprocess import Popen, PIPE
from asyncio import sleep
from bot.helper.ext_utils.message_utils import editMessage, sendMessage
from bot.helper.ext_utils.misc_utils import clean, get_rclone_config
from bot.helper.ext_utils.var_holder import get_rclone_var
from bot.helper.ext_utils.zip_utils import extract_file, get_path_size
from bot.helper.mirror_leech_utils.status_utils.extract_status import ExtractStatus
from bot.helper.mirror_leech_utils.status_utils.rclone_status import RcloneStatus
from bot.helper.mirror_leech_utils.status_utils.status_utils import MirrorStatus, TelegramClient
from bot.helper.mirror_leech_utils.status_utils.zip_status import ZipStatus
from bot.helper.mirror_leech_utils.upload_utils.telegram.telegram_uploader import TelegramUploader

class RcloneLeech:
    def __init__(self, message, user_id, origin_dir, dest_dir, file_name="", isZip=False, extract=False, pswd="", tag=None, folder= False):
        self.__message = message
        self.id = self.__message.id
        self._user_id= user_id
        self.__file_name= file_name
        self.__is_Zip = isZip
        self.__extract = extract
        self.__origin_path = origin_dir
        self.__dest_path = dest_dir
        self.__folder= folder
        self.__pswd = pswd
        self.__tag = tag
        self.suproc = None
        self.__rclone_pr= None

    async def leech(self):
        conf_path = get_rclone_config(self._user_id)
        leech_drive = get_rclone_var("LEECH_DRIVE", self._user_id)
        cmd = ['rclone', 'copy', f'--config={conf_path}', f'{leech_drive}:{self.__origin_path}', 
                          f'{self.__dest_path}', '-P']
        self.__rclone_pr = Popen(cmd, stdout=(PIPE),stderr=(PIPE))
        rclone_status= RcloneStatus(self.__rclone_pr, self.__message, self.__file_name)
        status= await rclone_status.progress(MirrorStatus.STATUS_DOWNLOADING, TelegramClient.PYROGRAM)
        if status:
            await self.__onDownloadComplete()
        else:
            await self.__onDownloadCancel()  

    async def __onDownloadComplete(self):
            if self.__folder:
                f_path = self.__dest_path 
                f_name= f_path.split("/")[-2]
                path = f"{f_path}{f_name}.zip" 
            else:
                f_path = self.__dest_path
                f_name= self.__file_name  
                path = f"{f_path}.zip"
            f_size = get_path_size(f_path) 
            if self.__is_Zip:
                LOGGER.info("Zipping...")  
                zip_sts= ZipStatus(f_name, f_size, self.__message, self)
                await zip_sts.create_message()
                if self.__pswd is not None:
                    if int(f_size) > TG_SPLIT_SIZE:
                        LOGGER.info(f'Zip: orig_path: {f_path}, zip_path: {path}.0*')
                        self.suproc = Popen(["7z", f"-v{TG_SPLIT_SIZE}b", "a", "-mx=0", f"-p{self.__pswd}", path, f_path])
                    else:
                        LOGGER.info(f'Zip: orig_path: {f_path}, zip_path: {path}')
                        self.suproc = Popen(["7z", "a", "-mx=0", f"-p{self.__pswd}", path, f_path])
                elif int(f_size) > TG_SPLIT_SIZE:
                    LOGGER.info(f'Zip: orig_path: {f_path}, zip_path: {path}.0*')
                    self.suproc = Popen(["7z", f"-v{TG_SPLIT_SIZE}b", "a", "-mx=0", path, f_path])
                else:
                    LOGGER.info(f'Zip: orig_path: {f_path}, zip_path: {path}')
                    self.suproc = Popen(["7z", "a", "-mx=0", path, f_path])
                self.suproc.wait()
                if self.suproc.returncode == -9:
                    return
                await tgUpload(path, self.__message, self.__tag) 
            elif self.__extract:
                LOGGER.info(f"Extracting...")
                ext_sts = ExtractStatus(f_name, f_size, self.__message, self)
                await ext_sts.create_message()
                if ospath.isdir(self.__dest_path):
                        for dirpath, _, files in walk(self.__dest_path, topdown=False):
                            for file in files:
                                if file.endswith((".zip", ".7z")) or search(r'\.part0*1\.rar$|\.7z\.0*1$|\.zip\.0*1$', file) \
                                or (file.endswith(".rar") and not search(r'\.part\d+\.rar$', file)):
                                    f_path = ospath.join(dirpath, file)
                                    if self.__pswd is not None:
                                        self.suproc = Popen(["7z", "x", f"-p{self.__pswd}", f_path, f"-o{dirpath}", "-aot"])
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
                                        del_path = ospath.join(dirpath, file_)
                                        remove(del_path)
                                await tgUpload(self.__dest_path, self.__message, self.__tag) 
                else:
                    path, msg= await extract_file(path, self.__message, self.__pswd)
                    if path == False:
                        return await sendMessage(msg, self.__message)
                    await tgUpload(path, self.__message, self.__tag) 
            else:
                await tgUpload(f_path, self.__message, self.__tag)
            clean(self.__dest_path)
    
    async def __onDownloadCancel(self):
        self.__rclone_pr.kill()
        await editMessage('Download cancelled', self.__message )

async def tgUpload(path, user_msg, tag):
    try:    
        tg_up= TelegramUploader(path, user_msg, tag)
        await tg_up.upload()
    except FloodWait as fw:
        await sleep(fw.seconds + 5)
        tg_up= TelegramUploader(path, user_msg, tag)
        await tg_up.upload()
    


        


           
