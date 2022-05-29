import asyncio
from configparser import ConfigParser
import os
from random import randrange
import re
import subprocess, time
from html import escape
from bot.core.get_vars import get_val
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils.drive_utils import get_glink
from bot.utils.get_rclone_conf import get_config
from bot.utils.misc_utils import clean_filepath, clean_path
from bot.utils.rename_file import rename
from bot import LOGGER

class RcloneMirror:
    def __init__(self, path, user_msg, new_name, tag, is_rename=False) -> None:
        self.id = self.__create_id(8)
        self.__path = path
        self.__user_msg = user_msg
        self.__new_name = new_name
        self.__tag = tag
        self.cancel = False
        self._is_rename = is_rename

    def __create_id(self, count):
        map = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        id = ''
        i = 0
        while i < count:
            rnd = randrange(len(map))
            id += map[rnd]
            i += 1
        return id

    async def mirror(self):
          old_path = self.__path
          path = ''
          dest_base = ''
          gen_drive_name = ''
          dest_drive = get_val('DEF_RCLONE_DRIVE')
          conf_path = await get_config()
          conf = ConfigParser()
          conf.read(conf_path)

          for i in conf.sections():
               if dest_drive == str(i):
                    if conf[i]['type'] == 'drive':
                         is_gdrive = True
                         dest_base = get_val('BASE_DIR')
                         LOGGER.info('Google Drive Upload Detected.')
                    else:
                         is_gdrive = False
                         gen_drive_name = conf[i]['type']
                         dest_base = get_val('BASE_DIR')
                         LOGGER.info(f"{gen_drive_name} Upload Detected.")
                    break
        
          if not os.path.exists(old_path):
               await self.__user_msg.reply('the path {path} not found')
               return
                
          if self._is_rename:
               path = await rename(old_path, self.__new_name)
          else:
               path = old_path

          if os.path.isdir(path):
            new_dest_base = os.path.join(dest_base, os.path.basename(path))
            rclone_copy_cmd = ['rclone', 'copy', f"--config={conf_path}", str(path),
                              f"{dest_drive}:{new_dest_base}", '-P']
          else:
            rclone_copy_cmd = ['rclone', 'copy', f"--config={conf_path}", str(path),
                              f"{dest_drive}:{dest_base}", '-P']
          
          self.__rclone_pr = subprocess.Popen(rclone_copy_cmd,
                stdout=(subprocess.PIPE),
                stderr=(subprocess.PIPE)
          )
          
          LOGGER.info('Uploading...')
          rcres = await self.__rclone_update()
          
          if rcres == False:
               self.__rclone_pr.kill()
               await self.__user_msg.edit('Mirror cancelled')
               return

          LOGGER.info('Successfully uploaded')

          name = os.path.basename(path)
          msg = 'Successfully uploaded ✅\n\n'
          msg += f"<b>Name: </b><code>{escape(name)}</code><b>"
          
          if os.path.isdir(path):
            if is_gdrive:
                gid = await get_glink(dest_drive, dest_base, os.path.basename(path), conf_path)
                folder_link = f"https://drive.google.com/folderview?id={gid[0]}"
                button = []
                button.append([InlineKeyboardButton(text='Drive Link', url=folder_link)])
                await self.__user_msg.edit(f"{msg}\n\n<b>cc: </b>{self.__tag}", reply_markup=(InlineKeyboardMarkup(button)))
            else:
                await self.__user_msg.edit(f"{msg}\n\n<b>cc: </b>{self.__tag}")
            clean_path(path)
          else:
            if is_gdrive:
                gid = await get_glink(dest_drive, dest_base, os.path.basename(path), conf_path, False)
                link = f"https://drive.google.com/file/d/{gid[0]}/view"
                button = []
                button.append([InlineKeyboardButton(text='Drive Link', url=link)])
                await self.__user_msg.edit(f"{msg}\n\n<b>cc: </b>{self.__tag}", reply_markup=(InlineKeyboardMarkup(button)))
            else:
                await self.__user_msg.edit(f"{msg}\n\n<b>cc: </b>{self.__tag}")
            clean_filepath(path)

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
                
                msg = '<b>{}...\n{} \n{} \nSpeed:- {} \nETA:- {}\n</b>'.format('Uploading...', nstr[0], prg, nstr[2], nstr[3].replace('ETA', ''))
                
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