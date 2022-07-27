import asyncio
from configparser import ConfigParser
import os
from random import randrange
import re
import subprocess, time
from html import escape
from bot.core.get_vars import get_val
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils.status_util.bottom_status import get_bottom_status
from bot.utils.bot_utils.drive_utils import get_glink
from bot.utils.bot_utils.misc_utils import clean_filepath, clean_path, get_rclone_config, rename_file
from bot import GLOBAL_RCLONE, LOGGER

class RcloneMirror:
    def __init__(self, path, user_msg, tag, new_name="", is_rename=False, torrent_name="") -> None:
        self.id = self.__create_id(8)
        self.__path = path
        self.__user_msg = user_msg
        self.__new_name = new_name
        self.torrent_name= torrent_name
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
          dest_base = ''
          is_gdrive= False
          general_drive_name = ''
          dest_drive = get_val('DEFAULT_RCLONE_DRIVE')
          conf_path = await get_rclone_config()
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
             self.__path = await rename_file(self.__path, self.__new_name)

          if os.path.isdir(self.__path):
                if len(self.torrent_name) > 0:
                    new_dest_base = os.path.join(dest_base, self.torrent_name)
                else:
                    new_dest_base = os.path.join(dest_base, os.path.basename(self.__path))

                rclone_copy_cmd = ['rclone', 'copy', f"--config={conf_path}", str(self.__path),
                                    f"{dest_drive}:{new_dest_base}", '-P']
                LOGGER.info(rclone_copy_cmd)
          else:
                rclone_copy_cmd = ['rclone', 'copy', f"--config={conf_path}", str(self.__path),
                                    f"{dest_drive}:{dest_base}", '-P']

          GLOBAL_RCLONE.add(self)
          self.__rclone_pr = subprocess.Popen(rclone_copy_cmd,
                stdout=(subprocess.PIPE),
                stderr=(subprocess.PIPE)
          )
          
          LOGGER.info('Uploading...')
          rcres = await self.__rclone_update()
          GLOBAL_RCLONE.remove(self)
          
          if rcres == False:
               self.__rclone_pr.kill()
               await self.__user_msg.edit('Mirror cancelled')
               if os.path.isdir(self.__path):
                    clean_path(self.__path) 
               else:
                    clean_filepath(self.__path)   
               return

          LOGGER.info('Successfully uploaded')

          if len(self.torrent_name) > 0:
            name = self.torrent_name
          else:
            name = os.path.basename(self.__path)
          msg = 'Successfully uploaded ✅\n\n'
          msg += f"<b>Name:</b><code>{escape(name)}</code>"
          
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
                
                msg = '**Name:** `{}`\n**Status:** {}\n{}\n**Uploaded:** {}\n**Speed:** {} | **ETA:** {}\n'.format(os.path.basename(self.__path), 'Uploading...', prg, nstr[0], nstr[2], nstr[3].replace('ETA', ''))
                msg += get_bottom_status() 

                if time.time() - start > edit_time:
                    if msg1 != msg:
                        start = time.time()
                        try:
                            await user_message.edit(text=msg, reply_markup=(InlineKeyboardMarkup([
                            [InlineKeyboardButton('Cancel', callback_data=(f"cancel_rclone_{self.id}".encode('UTF-8')))]
                            ])))                            
                        except:
                            pass
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