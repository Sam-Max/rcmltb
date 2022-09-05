from configparser import ConfigParser
from os import path as ospath
from subprocess import Popen, PIPE
from bot import LOGGER
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.helper.ext_utils.misc_utils import clean, get_rclone_config, rename_file
from bot.helper.ext_utils.rclone_utils import get_gid
from bot.helper.ext_utils.var_holder import get_rclone_var
from bot.helper.mirror_leech_utils.status_utils.rclone_status import RcloneStatus
from bot.helper.mirror_leech_utils.status_utils.status_utils import MirrorStatus, TelegramClient


class RcloneMirror:
    def __init__(self, path, message, tag, user_id, new_name="", is_rename=False):
        self.__path = path
        self.__message = message
        self.__user_id= user_id
        self.__new_name = new_name
        self.__tag = tag
        self.__is_rename = is_rename
        self.__dest_base = get_rclone_var('MIRRORSET_BASE_DIR', self.__user_id)
        self.__dest_drive = get_rclone_var('MIRRORSET_DRIVE', self.__user_id)
        self.__is_gdrive= False
        self.__rclone_pr= None

    async def mirror(self):
        conf_path = get_rclone_config(self.__user_id)
        conf = ConfigParser()
        conf.read(conf_path)
        
        if not ospath.exists(self.__path):
            LOGGER.info(f"Path does not not exist, Path: {self.__path}")
            return    

        for i in conf.sections():
            if self.__dest_drive == str(i):
                if conf[i]['type'] == 'drive':
                    self.__is_gdrive = True
                else:
                    self.__is_gdrive = False
                break

        if self.__is_rename:
            self.__path = rename_file(self.__path, self.__new_name)

        if ospath.isdir(self.__path):
            name= ospath.basename(self.__path) 
            new_dest_base = ospath.join(self.__dest_base, name)
            cmd = ['rclone', 'copy', f"--config={conf_path}", str(self.__path),
                                f"{self.__dest_drive}:{new_dest_base}", '-P']
        else:
            cmd = ['rclone', 'copy', f"--config={conf_path}", str(self.__path),
                                f"{self.__dest_drive}:{self.__dest_base}", '-P']

        self.__rclone_pr = Popen(cmd, stdout=(PIPE), stderr=(PIPE))
        rclone_status= RcloneStatus(self.__rclone_pr, self.__message, self.__path)
        status= await rclone_status.progress(status_type=MirrorStatus.STATUS_UPLOADING, 
                        client_type=TelegramClient.PYROGRAM)
        if status:
            await self.__onDownloadComplete(conf_path)
        else:
            await self.__onDownloadCancel()  
          
    async def __onDownloadComplete(self, conf_path):    
          msg = ""
          if ospath.isdir(self.__path):
                ent_name = ospath.basename(self.__path)
                msg += f"<b>Name: </b><code>{ent_name}</code>"
                if self.__is_gdrive:
                    gid = await get_gid(self.__dest_drive, self.__dest_base, f"{ent_name}/", conf_path)
                    folder_link = f"https://drive.google.com/folderview?id={gid[0]}"
                    button = []
                    button.append([InlineKeyboardButton(text='Drive Link', url=folder_link)])
                    await self.__message.edit(f"{msg}\n\n<b>cc: </b>{self.__tag}", reply_markup=(InlineKeyboardMarkup(button)))
                else:
                    await self.__message.edit(f"{msg}\n\n<b>cc: </b>{self.__tag}")
                clean(self.__path)
          else:
                _, ent_name = self.__path.rsplit('/', 1)     
                msg += f"<b>Name: </b><code>{ent_name}</code>"
                if self.__is_gdrive:
                    gid = await get_gid(self.__dest_drive, self.__dest_base, ent_name, conf_path, False)
                    link = f"https://drive.google.com/file/d/{gid[0]}/view"
                    button = []
                    button.append([InlineKeyboardButton(text='Drive Link', url=link)])
                    await self.__message.edit(f"{msg}\n\n<b>cc: </b>{self.__tag}", reply_markup=(InlineKeyboardMarkup(button)))
                else:
                    await self.__message.edit(f"{msg}\n\n<b>cc: </b>{self.__tag}")
                clean(self.__path)

    async def __onDownloadCancel(self):
        self.__rclone_pr.kill()
        await self.__message.edit('Download cancelled')
        clean(self.__path)    