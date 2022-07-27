#Modified from: (c) YashDK [yash-dk@github]

import asyncio, os
import time
import shutil
import aria2p
from psutil import cpu_percent, virtual_memory
from bot import LOGGER, uptime
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot import aria2
from bot.utils.bot_utils import human_format
from bot.utils.bot_utils.bot_utils import is_magnet
from bot.utils.bot_utils.human_format import get_readable_file_size

class AriaDownloader():
    def __init__(self, dl_link, user_message, new_file_name=None):
        super().__init__()
        self._aloop = asyncio.get_event_loop()
        self._dl_link = dl_link
        self._new_file_name = new_file_name 
        self._gid = 0
        self._user_message= user_message
        self._update_info = None

    async def add_url(self, aria_instance, text_url, path):
        download = await self._aloop.run_in_executor(None, aria_instance.add_uris, [text_url], {'dir': path})
        if download.error_message:
            error = str(download.error_message).replace('<', ' ').replace('>', ' ')
            return False, "**FAILED** \n" + error + "\n", None
        else:
            return True, "", download.gid

    async def execute(self):
        path= os.path.join(os.getcwd(), "Downloads", str(time.time()).replace(".","")) 
        if is_magnet(self._dl_link):
            err_message= "Not support for magnet links"
            return False, err_message, None  
        elif self._dl_link.lower().endswith(".torrent"):
            err_message= "Not support for .torrent files"
            return False, err_message, None  
        else:
            sagtus, err_message, gid = await self.add_url(aria2, self._dl_link, path)
            if not sagtus:
                return False, err_message, None 
            self._gid = gid
            statusr, error_message= await self.aria_progress_update()
            if not statusr:
               return False, error_message, None
            else:
                file = await self._aloop.run_in_executor(None, aria2.get_download, self._gid)
                file_path = os.path.join(file.dir, file.name)
                return True, error_message, file_path

    async def aria_progress_update(self):
        user_msg= self._user_message
        while True:
            try:
                download = await self._aloop.run_in_executor(None, aria2.get_download, self._gid)
                if download.followed_by_ids:
                    self._gid = download.followed_by_ids[0]
                self._update_info = download
                complete = download.is_complete
                update_message1= ""
                sleeps= False
                if not complete:
                    if not download.error_message:
                        if download is None:
                            error_message= "Error in fetching the direct DL"
                            return False, error_message
                        else:
                            sleeps = True
                            update_message= await self.create_update_message(download)
                            if update_message1 != update_message:
                                try:
                                    data = "cancel_aria2_{}".format(self._gid)
                                    await user_msg.edit(text=update_message, reply_markup=(InlineKeyboardMarkup([
                                            [InlineKeyboardButton('Cancel', callback_data=data.encode("UTF-8"))]
                                            ])))
                                    update_message1 = update_message
                                except Exception as e:
                                    pass

                            if sleeps:
                                if complete:
                                    await user_msg.edit("Completed")     
                                    break     
                                sleeps = False
                                await asyncio.sleep(2)
                    else:
                        msg = download.error_message
                        error_message = f"The aria download failed due to this reason:- {msg}"
                        return False, error_message
                else:
                    error_message= f"Download completed: `{download.name}` - (`{download.total_length_string()}`)"
                    return True, error_message
            except aria2p.client.ClientException as e:
                if " not found" in str(e) or "'file'" in str(e):
                    error_reason = "Aria download canceled."
                    return False, error_reason
                else:
                    LOGGER.warning("Error due to a client error.")
                pass
            except RecursionError:
                download.remove(force=True)
                error_reason = "The link is basically dead."
                return False, error_reason
            except Exception as e:
                LOGGER.info(str(e))
                self._is_errored = True
                if " not found" in str(e) or "'file'" in str(e):
                    error_reason = "Aria download canceled."
                    return False, error_reason
                else:
                    LOGGER.warning(str(e))
                    error_reason =  f"Error: {str(e)}"
                    return False, error_reason

    async def create_update_message(self, download):
        downloading_dir_name = "N/A"
        try:
            downloading_dir_name = str(download.name)
        except:
            pass
        bottom_status= ''
        diff = time.time() - uptime
        diff = human_format.human_readable_timedelta(diff)
        usage = shutil.disk_usage("/")
        free = human_format.human_readable_bytes(usage.free) 
        bottom_status += f"\n\n<b>CPU:</b> {cpu_percent()}% | <b>FREE:</b> {free}" + f"\n<b>RAM:</b> {virtual_memory().percent}% | <b>UPTIME:</b> {diff}"
        msg = "<b>Name:</b>{}\n".format(downloading_dir_name)
        msg += "<b>Status:</b> Downloading...\n"
        msg += "{}\n".format(self.get_progress_bar_string())
        msg += "<b>P:</b> {}%\n".format(round(download.progress, 2))
        msg += "<b>Downloaded:</b> {} <b>of:</b> {}\n".format(get_readable_file_size(download.completed_length), download.total_length_string())
        msg += "<b>Speed:</b> {}".format(download.download_speed_string()) + "|" + "<b>ETA: {} Mins\n</b>".format(download.eta_string())
        try:
            msg += f"<b>Seeders:</b> {download.num_seeders}" 
            msg += f" | <b>Peers:</b> {download.connections}"
        except:
            pass
        try:
            msg += f"<b>Seeders:</b> {download.num_seeds}"
            msg += f" | <b>Leechers:</b> {download.num_leechs}"
        except:
            pass
        msg += bottom_status
        return msg
    
    def get_progress_bar_string(self):
        completed = self._update_info.completed_length / 8
        total = self._update_info.total_length / 8
        p = 0 if total == 0 else round(completed * 100 / total)
        p = min(max(p, 0), 100)
        cFull = p // 8
        p_str = '■' * cFull
        p_str += '□' * (12 - cFull)
        p_str = f"[{p_str}]"
        return p_str

    async def remove_dl(self, gid):
        if gid is None:
            gid = self._gid
        try:
            download = await self._aloop.run_in_executor(None, aria2.get_download, gid)
            if download.is_waiting:
                aria2.remove([download], force=True, files=True)
                return
            if len(download.followed_by_ids) != 0:
                downloads = aria2.get_downloads(download.followed_by_ids)
                aria2.remove(downloads, force=True, files=True)
                aria2.remove([download], force=True, files=True)
                return
            aria2.remove([download], force=True, files=True)
            LOGGER.info("Download Removed")
        except Exception as e:
            LOGGER.exception(e)
            LOGGER.exception("Failed to Remove Download")
            pass

    def get_gid(self):
        return self._gid

    
    