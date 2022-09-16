import asyncio
from bot import LOGGER
from bot import aria2, status_dict, status_dict_lock
from bot.helper.ext_utils.bot_utils import is_magnet
from bot.helper.ext_utils.message_utils import editMessage, sendMessage
from bot.helper.mirror_leech_utils.status_utils.aria_status import AriaDownloadStatus

class Aria2Downloader():
    def __init__(self, link, message):
        super().__init__()
        self._loop = asyncio.get_event_loop()
        self.link = link
        self._gid = 0
        self.__message= message
        self.id= self.__message.id
        self._download= None

    async def execute(self, path):
        self.path= path
        args = {'dir': path, 'max-upload-limit': '1K'}

        if is_magnet(self.link):
            download = aria2.add_magnet(self.link, args)
        else :
            download = aria2.add_uris([self.link], args)

        if download.error_message:
            error = str(download.error_message).replace('<', ' ').replace('>', ' ')
            await sendMessage(error, self.__message)
            return False, None

        aria_status= AriaDownloadStatus(download.gid, self.__message)
        LOGGER.info("Aria2Download started...")
        status, rmsg, msg, name = await aria_status.create_status()
        if status:
            async with status_dict_lock:     
                del status_dict[self.id] 
            return True, rmsg, name
        else:
            await editMessage(msg, rmsg)    
            try:
                async with status_dict_lock:     
                    del status_dict[self.id] 
            except:
                pass
            return False, None, None    