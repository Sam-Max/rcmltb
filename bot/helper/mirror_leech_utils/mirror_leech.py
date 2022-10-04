from os import listdir, path as ospath, remove, walk
import os
from re import search
from bot import LOGGER, LEECH_SPLIT_SIZE, status_dict, status_dict_lock
from subprocess import Popen
from bot.helper.ext_utils.exceptions import NotSupportedExtractionArchive
from bot.helper.ext_utils.misc_utils import clean_target, rename_file
from bot.helper.ext_utils.zip_utils import get_base_name, get_path_size
from bot.helper.mirror_leech_utils.download_utils.rclone.rclone_mirror import RcloneMirror
from bot.helper.mirror_leech_utils.status_utils.extract_status import ExtractStatus
from bot.helper.mirror_leech_utils.status_utils.zip_status import ZipStatus
from bot.helper.mirror_leech_utils.upload_utils.telegram_uploader import TelegramUploader

class MirrorLeech:
    def __init__(self, path, message, tag, user_id, newName= None, isRename= False, isZip=False, extract=False, pswd=None, isLeech= False):
        self.__message = message
        self.id = self.__message.id
        self.__path = path
        self.__is_Zip = isZip
        self.__extract = extract
        self.__pswd = pswd
        self.__tag = tag
        self.__new_name= newName
        self.__isRename= isRename
        self.__user_id= user_id
        self.__isLeech= isLeech
        self.__is_extract= False
        self.__suproc = None

    async def execute(self):
        f_size = get_path_size(self.__path)
        async with status_dict_lock:
            try:  
                download = status_dict[self.id]
                path= self.__path
                name = str(download.name()).replace('/', '')
            except:
                path, name= self.__path.rsplit("/", 1)
        if name == "None" or not ospath.exists(f"{path}/{name}"):
            name = listdir(path)[-1]
        f_path= f"{path}/{name}" 
        if self.__is_Zip:
            path = f"{f_path}.zip" 
            zip_status= ZipStatus(name, f_size, self.__message, self)
            await zip_status.create_message()
            if self.__pswd is not None:
                if int(f_size) > LEECH_SPLIT_SIZE:
                    LOGGER.info(f'Zip: orig_path: {f_path}, zip_path: {path}.0*')
                    self.__suproc = Popen(["7z", f"-v{LEECH_SPLIT_SIZE}b", "a", "-mx=0", f"-p{self.__pswd}", path, f_path])
                else:
                    LOGGER.info(f'Zip: orig_path: {f_path}, zip_path: {path}')
                    self.__suproc = Popen(["7z", "a", "-mx=0", f"-p{self.__pswd}", path, f_path])
            elif int(f_size) > LEECH_SPLIT_SIZE:
                LOGGER.info(f'Zip: orig_path: {f_path}, zip_path: {path}.0*')
                self.__suproc = Popen(["7z", f"-v{LEECH_SPLIT_SIZE}b", "a", "-mx=0", path, f_path])
            else:
                LOGGER.info(f'Zip: orig_path: {f_path}, zip_path: {path}')
                self.__suproc = Popen(["7z", "a", "-mx=0", path, f_path])
            self.__suproc.wait()
            if self.__suproc.returncode == -9:
                return
            clean_target(f_path)
        elif self.__extract:
            try:
                self.__is_extract= True
                if ospath.isfile(f_path):
                    path = get_base_name(f_path)
                LOGGER.info(f"Extracting: {name}")
                ext_status = ExtractStatus(name, f_size, self.__message, self)
                await ext_status.create_message()
                if ospath.isdir(f_path):
                    path = f_path    
                    for dirpath, _, files in walk(f_path, topdown=False):
                        for file in files:
                            if search(r'\.part0*1\.rar$|\.7z\.0*1$|\.zip\.0*1$|\.zip$|\.7z$|^.(?!.*\.part\d+\.rar)(?=.*\.rar$)', file):
                                t_path = ospath.join(dirpath, file)
                                if self.__pswd is not None:
                                    self.__suproc = Popen(["7z", "x", f"-p{self.__pswd}", t_path, f"-o{dirpath}", "-aot"])
                                else:
                                    self.__suproc = Popen(["7z", "x", t_path, f"-o{dirpath}", "-aot"])
                                    self.__suproc.wait()
                                if self.__suproc.returncode == -9:
                                    return
                                elif self.__suproc.returncode != 0:
                                    LOGGER.error('Unable to extract archive splits!')
                        if self.__suproc is not None and self.__suproc.returncode == 0:
                            for file in files:
                                if search(r'\.r\d+$|\.7z\.\d+$|\.z\d+$|\.zip\.\d+$|\.zip$|\.rar$|\.7z$', file):
                                    del_path = ospath.join(dirpath, file)
                                    try:
                                        remove(del_path)
                                    except:
                                        return
                else:
                    if self.__pswd is not None:
                        self.__suproc = Popen(["7z", "x", f"-p{self.__pswd}", f_path, f"-o{path}", "-aot"])
                    else:
                        self.__suproc = Popen(["7z", "x", f_path, f"-o{path}", "-aot"])
                    self.__suproc.wait()
                    if self.__suproc.returncode == -9:
                        return
                    elif self.__suproc.returncode == 0:
                        LOGGER.info(f"Extracted Path: {path}")
                        try:
                            os.remove(f_path)
                        except:
                            return
                    else:
                        LOGGER.error('Unable to extract archive! Uploading anyway')
                        path = f_path
            except NotSupportedExtractionArchive:
                LOGGER.info("Not any valid archive, uploading file as it is.")
                path = f_path
        else:
            if self.__isRename:
                path = rename_file(f_path, self.__new_name) 
            else:
                path= f_path 
        up_dir, up_name = path.rsplit('/', 1)
        if self.__isLeech:
            tg_up= TelegramUploader(up_dir, up_name, f_size, self.__message, self.__tag)
            await tg_up.upload()
        else:
            rc_mirror = RcloneMirror(up_dir, up_name, self.__message, self.__tag, self.__user_id, isExtract= self.__is_extract)
            await rc_mirror.mirror()
        async with status_dict_lock: 
            try:  
                del status_dict[self.id]
            except:
                pass
