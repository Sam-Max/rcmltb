from configparser import ConfigParser
import os
import subprocess
from subprocess import Popen 
from bot.core.get_vars import get_val
from bot.utils.status_utils.misc_utils import MirrorStatus, TelegramClient
from bot.utils.status_utils.rclone_status import RcloneStatus
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils.bot_utils.drive_utils import get_glink
from bot.utils.bot_utils.misc_utils import clean,get_rclone_config, rename_file



class RcloneMirror:
    def __init__(self, path, user_msg, tag, new_name="", torrent_name="", is_rename=False):
        self.__path = path
        self.__user_msg = user_msg
        self.__new_name = new_name
        self.__tag = tag
        self.__torrent_name= torrent_name
        self.__is_rename = is_rename
        self.__dest_base = ""
        self.__dest_drive = get_val('DEFAULT_RCLONE_DRIVE')
        self.__is_gdrive= False
        self.__rclone_pr= None

    async def __onDownloadStart(self, conf_path):
          if self.__is_rename:
              self.__path = rename_file(self.__path, self.__new_name)

          if len(self.__torrent_name) > 0:
              name = self.__torrent_name
          else:
              name = os.path.basename(self.__path)

          if os.path.isdir(self.__path):
            if len(self.__torrent_name) > 0:
                new_dest_base = os.path.join(self.__dest_base, self.__torrent_name)
            else:
                new_dest_base = os.path.join(self.__dest_base, os.path.basename(self.__path))

            cmd = ['rclone', 'copy', f"--config={conf_path}", str(self.__path),
                                f"{self.__dest_drive}:{new_dest_base}", '-P']
          else:
            cmd = ['rclone', 'copy', f"--config={conf_path}", str(self.__path),
                                f"{self.__dest_drive}:{self.__dest_base}", '-P']

          self.__rclone_pr = Popen(cmd, stdout=(subprocess.PIPE),stderr=(subprocess.PIPE))
          rclone_status= RcloneStatus(self.__rclone_pr, self.__user_msg, name)
          status= await rclone_status.progress(
                            status_type=MirrorStatus.STATUS_UPLOADING, 
                            client_type=TelegramClient.PYROGRAM)
          if status:
             await self.__onDownloadComplete(conf_path, name)
          else:
             clean(self.__path)      

    async def __onDownloadComplete(self, conf_path, name):    
          msg = f"<b>Name: </b><code>{name}</code>"
          if os.path.isdir(self.__path):
                if len(self.__torrent_name) > 0:
                    gid = await get_glink(self.__dest_drive, self.__dest_base, self.__torrent_name, conf_path)
                else:
                    gid = await get_glink(self.__dest_drive, self.__dest_base, os.path.basename(self.__path), conf_path)
                if self.__is_gdrive:
                    folder_link = f"https://drive.google.com/folderview?id={gid[0]}"
                    button = []
                    button.append([InlineKeyboardButton(text='Drive Link', url=folder_link)])
                    await self.__user_msg.edit(f"{msg}\n\n<b>cc: </b>{self.__tag}", reply_markup=(InlineKeyboardMarkup(button)))
                else:
                    await self.__user_msg.edit(f"{msg}\n\n<b>cc: </b>{self.__tag}")
                clean(self.__path)
          else:
                if self.__is_gdrive:
                    gid = await get_glink(self.__dest_drive, self.__dest_base, os.path.basename(self.__path), conf_path, False)
                    link = f"https://drive.google.com/file/d/{gid[0]}/view"
                    button = []
                    button.append([InlineKeyboardButton(text='Drive Link', url=link)])
                    await self.__user_msg.edit(f"{msg}\n\n<b>cc: </b>{self.__tag}", reply_markup=(InlineKeyboardMarkup(button)))
                else:
                    await self.__user_msg.edit(f"{msg}\n\n<b>cc: </b>{self.__tag}")
                clean(self.__path)

    async def mirror(self):
        conf_path = get_rclone_config()
        conf = ConfigParser()
        conf.read(conf_path)

        for i in conf.sections():
            if self.__dest_drive == str(i):
                if conf[i]['type'] == 'drive':
                    self.__is_gdrive = True
                    self.__dest_base = get_val('BASE_DIR')
                else:
                    self.__is_gdrive = False
                    self.__dest_base = get_val('BASE_DIR')
                break

        await self.__onDownloadStart(conf_path)
          
          

          
        
          

          
    
    