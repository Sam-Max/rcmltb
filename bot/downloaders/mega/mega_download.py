import shutil
from subprocess import Popen
import time
from psutil import cpu_percent, virtual_memory
from bot import DOWNLOAD_DIR, LOGGER, uptime
from bot.core.get_vars import get_val
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils import human_format
from bot.utils.human_format import human_readable_bytes
from megasdkrestclient import MegaSdkRestClient, errors, constants
import asyncio
import os
from functools import partial


class MegaDownloader():
    CLI_LIST = []
    def __init__(self, link, user_message):
        super().__init__()
        self._client = None 
        self._process = None
        self._link = link
        self._user_message = user_message
        self._update_info = None
        self._gid = 0
        self._aloop = asyncio.get_event_loop()

    async def init_mega_client(self, return_pr=False):
        if len(self.CLI_LIST) > 0:
            if return_pr:
                return self.CLI_LIST[1]
            else:
                return self.CLI_LIST[0]
        
        if self._client is None and self._process is None:
            MEGA_API_KEY = get_val("MEGA_API_KEY")
            MEGA_UNAME = get_val("MEGA_UNAME")
            MEGA_PASSWORD = get_val("MEGA_PASSWORD")
            
            if MEGA_API_KEY is None:
                 return None

            process = Popen(["megasdkrest", "--apikey", MEGA_API_KEY, "--port", "8200"])
            await asyncio.sleep(5)
            mega_client = MegaSdkRestClient("http://localhost:8200")
            
            anon = False
            if MEGA_UNAME is None:
                anon = True
                LOGGER.warn("Mega Username not specified")
            
            if MEGA_PASSWORD is None:
                anon = True
                LOGGER.warn("Mega Password not specified")
            
            if anon:
                LOGGER.info("Mega running in Anon mode.")
            else:
                LOGGER.info("Mega running in Logged in mode.")
                
                try:
                    mega_client.login(MEGA_UNAME, MEGA_PASSWORD)
                except:
                    LOGGER.error("Mega login failed.")
                    LOGGER.info("Started in anon mode.")

            self._client = mega_client
            self._process = process
            self.CLI_LIST.append(mega_client)
            self.CLI_LIST.append(process)
        
        if return_pr:
            return self._process
        else:
            return self._client

    async def execute(self):
        mega_client = await self.init_mega_client()
        try:
            dl_add_info = await self._aloop.run_in_executor(None, partial(mega_client.addDl, self._link, DOWNLOAD_DIR))
        except errors.MegaSdkRestClientException as e:
            error_reason = str(dict(e.message)["message"]).title()
            return False, error_reason, None

        LOGGER.info("MegaDL Task Running....")
        self._gid  = dl_add_info["gid"]
        dl_info = await self._aloop.run_in_executor(None, partial(mega_client.getDownloadInfo,dl_add_info["gid"]))
        self._path = os.path.join(dl_add_info["dir"], dl_info["name"])

        while True:
            dl_info = await self._aloop.run_in_executor(None, partial(mega_client.getDownloadInfo, dl_add_info["gid"]))
            
            if dl_info["state"] not in [constants.State.TYPE_STATE_CANCELED, constants.State.TYPE_STATE_FAILED]:
                if dl_info["state"] == constants.State.TYPE_STATE_COMPLETED:
                    error_reason = "Download Complete."
                    await asyncio.sleep(2)
                    return True, error_reason, self._path

                try:
                    self._update_info = dl_info
                    await self.aria_progress_update()
                except Exception as e:
                    LOGGER.info(e)
            else:
                if dl_info["state"] == constants.State.TYPE_STATE_CANCELED:
                    error_reason = "Mega download canceled"
                    return False, error_reason, None
                else:
                    error_reason = dl_info["error_string"]
                return False, error_reason, None

    async def aria_progress_update(self):
        update_message1= ""
        sleeps= False
        
        if self._update_info is not None:
            sleeps = True
            update_message = await self.create_update_message()
            if update_message1 != update_message:
               try:
                    data = "cancel_megadl_{}".format(self.get_gid())
                    await self._user_message.edit(text=update_message, reply_markup=(InlineKeyboardMarkup([
                                            [InlineKeyboardButton('Cancel', callback_data=data.encode("UTF-8"))]
                                            ])))
               except Exception:
                    pass
               if sleeps:
                    sleeps = False
                    await asyncio.sleep(5)
                    
    async def create_update_message(self):
        update= self._update_info
        bottom_status= ''
        diff = time.time() - uptime
        diff = human_format.human_readable_timedelta(diff)
        usage = shutil.disk_usage("/")
        free = human_format.human_readable_bytes(usage.free) 
        bottom_status += f"\n<b>CPU:</b> {cpu_percent()}% | <b>FREE:</b> {free}" + f"\n<b>RAM:</b> {virtual_memory().percent}% | <b>UPTIME:</b> {diff}"

        msg =  "<b>Name:</b> {}\n".format(update["name"])
        msg += "<b>Status:</b> Downloading...\n"
        msg += "{}\n".format(self.progress_bar((update["completed_length"]/update["total_length"])))
        msg += "<b>P:</b> {}%\n".format(round((update["completed_length"]/update["total_length"])*100, 2))
        msg += "<b>Downloaded:</b> {} of {}\n".format(human_readable_bytes(update["completed_length"]),
            human_readable_bytes(update["total_length"]))
        msg += "<b>Speed:</b> {}".format(human_readable_bytes(update["speed"])) + "|" + "<b>ETA:</b> <b>N/A</b>\n"
        msg += bottom_status
        return msg

    def progress_bar(self, percentage):
        """Returns a progress bar for download
        """
        #percentage is on the scale of 0-1
        comp ="▪️"
        ncomp ="▫️"
        pr = ""

        for i in range(1,11):
            if i <= int(percentage*10):
                pr += comp
            else:
                pr += ncomp
        return pr

    async def remove_mega_dl(self, gid):
        mega_client = await self.init_mega_client()
        await self._aloop.run_in_executor(None, partial(mega_client.cancelDl, gid))

    def get_gid(self):
        return self._gid
