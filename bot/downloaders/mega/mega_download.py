#Modified from: (c) YashDK [yash-dk@github]

import pathlib
import shutil
import time
from psutil import cpu_percent, virtual_memory
from bot import LOGGER, uptime
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils.bot_utils import human_format
from bot.utils.bot_utils.human_format import human_readable_bytes
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
        self.__mega_client = MegaSdkRestClient('http://localhost:6090')
        self._user_message = user_message
        self._update_info = None
        self._gid = 0
        self._aloop = asyncio.get_event_loop()

    async def execute(self):
        path= os.path.join(os.getcwd(), "Downloads", str(time.time()).replace(".","")) 
        pathlib.Path(path).mkdir(parents=True, exist_ok=True)
        
        try:
            dl_add_info = await self._aloop.run_in_executor(None, partial(self.__mega_client.addDl, self._link, path))
        except errors.MegaSdkRestClientException as e:
            error_reason = str(dict(e.message)["message"]).title()
            return False, error_reason, None

        LOGGER.info("MegaDL Task Running....")
        self._gid  = dl_add_info["gid"]
        dl_info = await self._aloop.run_in_executor(None, partial(self.__mega_client.getDownloadInfo,dl_add_info["gid"]))
        self._path = os.path.join(dl_add_info["dir"], dl_info["name"])

        while True:
            dl_info = await self._aloop.run_in_executor(None, partial(self.__mega_client.getDownloadInfo, dl_add_info["gid"]))
            
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
                    return False, error_reason, self._path
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
        await self._aloop.run_in_executor(None, partial(self.__mega_client.cancelDl, gid))

    def get_gid(self):
        return self._gid
