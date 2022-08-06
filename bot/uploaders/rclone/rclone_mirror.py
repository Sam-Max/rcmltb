from configparser import ConfigParser
import os
import subprocess
from subprocess import Popen 
from bot.core.get_vars import get_val
from bot.utils.status_utils.misc_utils import MirrorStatus
from bot.utils.status_utils.rclone_status import RcloneStatus
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils.bot_utils.drive_utils import get_glink
from bot.utils.bot_utils.misc_utils import clean_filepath, clean_path, get_rclone_config, rename_file
from bot import LOGGER



class RcloneMirror:
    def __init__(self, path, user_msg, tag, new_name="", is_rename=False, torrent_name="") -> None:
        self.__path = path
        self.__user_msg = user_msg
        self.__new_name = new_name
        self.torrent_name= torrent_name
        self.__tag = tag
        self._is_rename = is_rename

    async def mirror(self):
          dest_base = ''
          is_gdrive= False
          general_drive_name = ''
          dest_drive = get_val('DEFAULT_RCLONE_DRIVE')
          conf_path = get_rclone_config()
          conf = ConfigParser()
          conf.read(conf_path)

          for i in conf.sections():
               if dest_drive == str(i):
                    if conf[i]['type'] == 'drive':
                         is_gdrive = True
                         dest_base = get_val('BASE_DIR')
                         LOGGER.info('Google Drive Unit Detected...')
                    else:
                         is_gdrive = False
                         general_drive_name = conf[i]['type']
                         dest_base = get_val('BASE_DIR')
                         LOGGER.info(f"{general_drive_name} Unit Detected...")
                    break
        
          if not os.path.exists(self.__path):
               return await self.__user_msg.reply('the path {path} not found')
                
          if self._is_rename:
                self.__path = rename_file(self.__path, self.__new_name)

          if len(self.torrent_name) > 0:
                name = self.torrent_name
          else:
                name = os.path.basename(self.__path)

          if os.path.isdir(self.__path):
                if len(self.torrent_name) > 0:
                    new_dest_base = os.path.join(dest_base, self.torrent_name)
                else:
                    new_dest_base = os.path.join(dest_base, os.path.basename(self.__path))

                rclone_copy_cmd = ['rclone', 'copy', f"--config={conf_path}", str(self.__path),
                                    f"{dest_drive}:{new_dest_base}", '-P']
          else:
                rclone_copy_cmd = ['rclone', 'copy', f"--config={conf_path}", str(self.__path),
                                    f"{dest_drive}:{dest_base}", '-P']

          self.__rclone_pr = Popen(rclone_copy_cmd, stdout=(subprocess.PIPE),stderr=(subprocess.PIPE))
          rclone_status= RcloneStatus(self.__rclone_pr, self.__user_msg, name)
          status= await rclone_status.progress(status_type=MirrorStatus.STATUS_UPLOADING, 
                                               client_type='pyrogram')
          
          if status == False:
               if os.path.isdir(self.__path):
                    clean_path(self.__path) 
               else:
                    clean_filepath(self.__path)   
               return

          msg = f"<b>Name: </b><code>{name}</code>"

          if os.path.isdir(self.__path):
                if len(self.torrent_name) > 0:
                    gid = await get_glink(dest_drive, dest_base, self.torrent_name, conf_path)
                else:
                    gid = await get_glink(dest_drive, dest_base, os.path.basename(self.__path), conf_path)
                if is_gdrive:
                    folder_link = f"https://drive.google.com/folderview?id={gid[0]}"
                    button = []
                    button.append([InlineKeyboardButton(text='Drive Link', url=folder_link)])
                    await self.__user_msg.edit(f"{msg}\n\n<b>cc: </b>{self.__tag}", reply_markup=(InlineKeyboardMarkup(button)))
                else:
                    await self.__user_msg.edit(f"{msg}\n\n<b>cc: </b>{self.__tag}")
                clean_path(self.__path)
          else:
                if is_gdrive:
                    gid = await get_glink(dest_drive, dest_base, os.path.basename(self.__path), conf_path, False)
                    link = f"https://drive.google.com/file/d/{gid[0]}/view"
                    button = []
                    button.append([InlineKeyboardButton(text='Drive Link', url=link)])
                    await self.__user_msg.edit(f"{msg}\n\n<b>cc: </b>{self.__tag}", reply_markup=(InlineKeyboardMarkup(button)))
                else:
                    await self.__user_msg.edit(f"{msg}\n\n<b>cc: </b>{self.__tag}")
                clean_filepath(self.__path)
    
    