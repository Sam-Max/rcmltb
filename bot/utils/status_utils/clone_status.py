from asyncio import sleep
import re
from pyrogram.errors.exceptions import FloodWait, MessageNotModified
from bot import  LOGGER
from bot.utils.bot_utils.message_utils import editMessage
from bot.utils.status_utils.status_utils import MirrorStatus, get_bottom_status
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton



class CloneStatus:
     def __init__(self, process, message, name):
        self._process = process
        self._message = message
        self.id = self._message.id
        self.name= name

     async def progress(self, status_type, client_type):
          try:
               stdout, stderr = await self._process.communicate()
               err = stderr.decode()
          except 'userRateLimitExceeded' in Exception:
               return await editMessage("‼️ **ERROR** ‼️\n\n Error 403: User rate limit exceeded.", self._message)
          except Exception as err:
               return await editMessage(f"‼️ **ERROR** ‼️\n\n {err}", self._message)

          data = stderr.decode()
          mat = re.findall('Transferred:.*ETA.*', data)
          
          if mat is not None and len(mat) > 0:
               nstr = mat[0].replace('Transferred:', '')
               nstr = nstr.strip()
               nstr = nstr.split(',')

               if status_type == MirrorStatus.STATUS_CLONING:
                    status_msg = '**Name:** `{}`\n**Status:** {}\n**Downloaded:** {}\n**Speed:** {} | **ETA:** {}\n'.format(
                                        self.name, status_type, nstr[0], nstr[2], nstr[3].replace('ETA', ''))
                    status_msg += get_bottom_status()

                    if client_type == 'pyrogram':
                         try:
                              await editMessage(status_msg, self._message, reply_markup=(InlineKeyboardMarkup([
                              [InlineKeyboardButton('Cancel', callback_data=(f"cancel_rclone_{self.id}".encode('UTF-8')))]
                              ])))
                         except FloodWait as fw:
                              LOGGER.warning(f"FloodWait : Sleeping {fw.value}s")
                              await sleep(fw.value)
                         except MessageNotModified:
                              await sleep(1)
          
          #Get file name  
          try:
               if len(self.name) == 0:
                    pattern = "INFO(.*)(:)(.*)(:) (Copied)"
                    name = re.findall(pattern, data)
                    file_name = name[0][2].strip()
                    return True, file_name 
               else:
                    return True, "" 
          except IndexError:
               await editMessage(f"**ERROR**\n\nTry Any Other URL or Try Again", self._message)
               return True, "" 
          except Exception as err:
               LOGGER.info(err)
               await editMessage(f"**ERROR**\n\n`{err}`", self._message)
               return True, "" 
                    
