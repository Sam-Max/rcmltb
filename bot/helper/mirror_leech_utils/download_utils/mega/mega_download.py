from pathlib import Path
from bot import LOGGER
from bot.helper.ext_utils.bot_utils import setInterval
from bot.helper.ext_utils.message_utils import sendMessage
from bot.helper.mirror_leech_utils.status_utils.mega_status import MegaDownloadStatus
from megasdkrestclient import MegaSdkRestClient, constants


class MegaDownloader():
    POLLING_INTERVAL = 3

    def __init__(self, link, message):
        super().__init__()
        self._link = link
        self.mega_client = MegaSdkRestClient('http://localhost:6090')
        self._message = message
        self.id= self._message.id
        self.__periodic= None
        self.is_cancelled= False
        self.is_completed= False

    async def execute(self, path):
        Path(path).mkdir(parents=True, exist_ok=True)
        LOGGER.info("Mega Download Started...")
        try:
            dl = self.mega_client.addDl(self._link, path)
        except Exception as e:
            error_reason = str(dict(e.message)["message"]).title()
            await sendMessage(error_reason, self._message)
            return False, None, ""

        gid = dl["gid"]
        self.gid= gid
        self.__periodic = setInterval(self.POLLING_INTERVAL, self.__onInterval)
        mega_status= MegaDownloadStatus(gid, self._message, self)
        status, rmsg, path= await mega_status.create_status()
        if status:
            return True, rmsg, path  
        else:
            return False, rmsg, ""       

    def __onInterval(self):
        dlInfo = self.mega_client.getDownloadInfo(self.gid)
        name = dlInfo['name']
        if dlInfo['state'] in [constants.State.TYPE_STATE_COMPLETED, constants.State.TYPE_STATE_CANCELED, 
            constants.State.TYPE_STATE_FAILED] and self.__periodic is not None:
            self.__periodic.cancel()
        if dlInfo['state'] == constants.State.TYPE_STATE_COMPLETED:
            self.is_completed= True
            return
        if dlInfo['state'] == constants.State.TYPE_STATE_CANCELED:
            LOGGER.info(f"Cancelling Download: {name}, cause: 'Download stopped by user!'")
            self.is_cancelled= True
            return
        if dlInfo['state'] == constants.State.TYPE_STATE_FAILED:
            LOGGER.info(f"Cancelling Download: {name}, cause: {dlInfo['error_string']}'")
            self.is_cancelled= True
            return
    

