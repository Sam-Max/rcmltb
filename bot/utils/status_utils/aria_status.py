from asyncio import sleep
from time import time
import aria2p 
from bot import EDIT_SLEEP_SECS, aria2, status_dict, status_dict_lock, LOGGER
from bot.utils.bot_utils.human_format import get_readable_file_size
from bot.utils.bot_utils.message_utils import editMessage, sendMessage
from bot.utils.status_utils.status_utils import MirrorStatus, get_bottom_status
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors.exceptions import FloodWait, MessageNotModified

def get_download(gid):
    return aria2.get_download(gid)

class AriaDownloadStatus:
    def __init__(self, gid, message):
        self.__gid = gid
        self.__message= message
        self.id= self.__message.id
        self._status_msg= ""

    def __update(self):
        self.__download = get_download(self.__gid)
        if self.__download.followed_by_ids:
            self.__gid = self.__download.followed_by_ids[0]

    def get_status_msg(self):
         return self._status_msg     

    async def create_status(self):
          async with status_dict_lock:
              status_dict[self.id] = self
          rmsg= await sendMessage("Starting Download", self.__message)
          sleeps= False
          start = time()
          while True:
                try:
                    self.__update()
                    complete= self.__download.is_complete 
                    if not complete:
                        if not self.__download.error_message:
                            sleeps = True
                            self._status_msg= self.create_status_message()
                            if time() - start > EDIT_SLEEP_SECS:
                                try:
                                    data = "cancel_aria2_{}".format(self.__gid)
                                    await editMessage(self._status_msg, rmsg, reply_markup= InlineKeyboardMarkup([
                                                [InlineKeyboardButton('Cancel', callback_data=data.encode("UTF-8"))]
                                                ]))
                                except FloodWait as fw:
                                        await sleep(fw.value)
                                except MessageNotModified:
                                        await sleep(1)
                                if sleeps:
                                    sleeps = False
                                    await sleep(2)
                        else:
                            msg = self.__download.error_message
                            msg = f"Download failed:- {msg}"
                            return False, rmsg, msg, ""
                    else:
                        LOGGER.info("Download completed!")
                        msg = "Download completed!"
                        return True, rmsg, msg, self.__download.name
                except aria2p.client.ClientException as ex: 
                    if " not found" in str(ex) or "'file'" in str(ex):
                        msg = "Download cancelled"
                        return False, rmsg, msg, ""
                    else:
                        msg = "Error due to a client error"
                        return False, rmsg, msg, ""
                except Exception as ex:
                    if " not found" in str(ex) or "'file'" in str(ex):
                        msg = "Download cancelled"
                        return False, rmsg, msg, ""
                    else:
                        msg = f"Download failed:- {str(ex)}"  
                        return False, rmsg, msg, ""

    def create_status_message(self):     
        downloading_dir_name = "N/A"
        try:
            downloading_dir_name = str(self.__download.name)
        except:
            pass
        msg = "<b>Name:</b>{}\n".format(downloading_dir_name)
        msg += "<b>Status:</b>{}\n".format(self.status())
        msg += "{}\n".format(self.get_progress_bar_string())
        msg += "<b>P:</b> {}%\n".format(round(self.__download.progress, 2))
        msg += "<b>Downloaded:</b> {} <b>of:</b> {}\n".format(get_readable_file_size(self.__download.completed_length), self.__download.total_length_string())
        msg += "<b>Speed:</b> {}".format(self.__download.download_speed_string()) + "|" + "<b>ETA: {} Mins\n</b>".format(self.__download.eta_string())
        try:
            msg += f"<b>Seeders:</b> {self.__download.num_seeders}" 
            msg += f" | <b>Peers:</b> {self.__download.connections}\n"
        except:
            pass
        try:
            msg += f"<b>Seeders:</b> {self.__download.num_seeds}"
            msg += f" | <b>Leechers:</b> {self.__download.num_leechs}\n"
        except:
            pass
        msg += get_bottom_status()
        return msg

    def get_progress_bar_string(self):
        completed = self.__download.completed_length / 8
        total = self.__download.total_length / 8
        p = 0 if total == 0 else round(completed * 100 / total)
        p = min(max(p, 0), 100)
        cFull = p // 8
        p_str = '■' * cFull
        p_str += '□' * (12 - cFull)
        p_str = f"[{p_str}]"
        return p_str
        
    def status(self):
        download = self.__download
        if download.is_waiting:
            return MirrorStatus.STATUS_WAITING
        elif download.is_paused:
            return MirrorStatus.STATUS_PAUSED
        else:
            return MirrorStatus.STATUS_DOWNLOADING

    def download(self):
        return self

    def gid(self):
        return self.__gid

    def cancel_download(self):
        self.__update()     
        if self.__download.is_waiting:
            aria2.remove([self.__download], force=True, files=True)
            return
        if len(self.__download.followed_by_ids) != 0:
            LOGGER.info(f"Removing Download.")
            downloads = aria2.get_downloads(self.__download.followed_by_ids)
            aria2.remove(downloads, force=True, files=True)
        else:
            LOGGER.info(f"Removing Download.")
        del status_dict[self.id]
        aria2.remove([self.__download], force=True, files=True)