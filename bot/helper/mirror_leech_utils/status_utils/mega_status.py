from time import time
from asyncio import sleep
from bot import EDIT_SLEEP_SECS
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.helper.ext_utils.human_format import human_readable_bytes
from bot.helper.ext_utils.message_utils import editMarkup, editMessage, sendMarkup
from bot.helper.mirror_leech_utils.status_utils.status_utils import MirrorStatus, get_bottom_status


def get_download_info(mega_client, gid):
    dl_info = mega_client.getDownloadInfo(gid) 
    return dl_info

class MegaDownloadStatus:
     def __init__(self, gid, message, obj):
        self.__gid = gid
        self.message= message
        self.id = self.message.id
        self._status_msg= ""
        self._obj= obj
        self._client= self._obj.mega_client
        self._dl_info= get_download_info(self._client, gid)

     def get_status_msg(self):
          return self._status_msg     

     def status(self) -> str:
        return MirrorStatus.STATUS_DOWNLOADING

     async def create_status(self):
        status_msg = await self.create_update_message() 
        keyboard= InlineKeyboardMarkup([[InlineKeyboardButton('Cancel', callback_data= "cancel {}".format(self.gid()))]]) 
        rmsg= await sendMarkup(status_msg, self.message, reply_markup=keyboard)
        sleeps= False
        start = time()
        while True:
               self._dl_info = get_download_info(self._client, self.__gid)
               if self._dl_info is not None:
                    sleeps = True
                    self._status_msg = await self.create_update_message()
                    if time() - start > EDIT_SLEEP_SECS:
                         await editMarkup(self._status_msg, rmsg, reply_markup=keyboard)
                         if sleeps:
                              if self._obj.is_cancelled:
                                   await editMessage("Download Cancelled", rmsg)
                                   return False, rmsg, None
                              if self._obj.is_completed:
                                   name = self._dl_info["name"]
                                   return True, rmsg, name
                              sleeps = False
                              await sleep(1)

     async def create_update_message(self):
        download = self._dl_info
        msg =  "<b>Name:</b> {}\n".format(download["name"])
        msg += f"<b>Status:</b> {MirrorStatus.STATUS_DOWNLOADING}\n"
        msg += "{}\n".format(self.__get_progress_bar(download["completed_length"], download["total_length"]))
        msg += "<b>P:</b> {}%\n".format(round((download["completed_length"]/download["total_length"])*100, 2))
        msg += "<b>Downloaded:</b> {} of {}\n".format(human_readable_bytes(download["completed_length"]),
            human_readable_bytes(download["total_length"]))
        msg += "<b>Speed:</b> {}".format(human_readable_bytes(download["speed"])) + "|" + "<b>ETA:</b> <b>N/A</b>\n"
        msg += get_bottom_status()
        return msg

     def __get_progress_bar(self, completed_length, total_length):
          completed = completed_length / 8
          total = total_length / 8
          p = 0 if total == 0 else round(completed * 100 / total)
          p = min(max(p, 0), 100)
          cFull = p // 8
          p_str = '■' * cFull
          p_str += '□' * (12 - cFull)
          p_str = f"[{p_str}]"
          return p_str
     
     def gid(self):
        return self.__gid

     def cancel_download(self):
        self._obj.mega_client.cancelDl(self.gid())