from asyncio import create_subprocess_exec
from asyncio.subprocess import PIPE
from random import SystemRandom
from string import ascii_letters, digits
from bot.helper.ext_utils.message_utils import sendStatusMessage
from bot.helper.ext_utils.misc_utils import get_rclone_config
from bot.helper.ext_utils.var_holder import get_rclone_val
from bot import LOGGER, status_dict, status_dict_lock
from bot.helper.mirror_leech_utils.status_utils.rclone_status import RcloneStatus
from bot.helper.mirror_leech_utils.status_utils.status_utils import MirrorStatus

class RcloneLeech:
    def __init__(self, origin_dir, dest_dir, listener, isFolder= False):
        self.__listener= listener
        self.__user_id= listener.user_id
        self.__origin_path = origin_dir
        self.__dest_path = dest_dir
        self.__isFolder= isFolder
        self.size= 0
        self.name= ""
        self.status_type= MirrorStatus.STATUS_DOWNLOADING
        self.process= None

    async def leech(self):
        conf_path = get_rclone_config(self.__user_id)
        LOGGER.info(conf_path)
        leech_drive = get_rclone_val("LEECH_DRIVE", self.__user_id)
        cmd = ['rclone', 'copy', f'--config={conf_path}', f'{leech_drive}:{self.__origin_path}', f'{self.__dest_path}', '-P']
        gid = ''.join(SystemRandom().choices(ascii_letters + digits, k=10)) 
        if self.__isFolder:
            self.name = self.__dest_path.rsplit("/", 2)[1]
        else:
            self.name = self.__dest_path.rsplit("/", 1)[1]
        async with status_dict_lock:
            status = RcloneStatus(self, gid)
            status_dict[self.__listener.uid] = status
        await sendStatusMessage(self.__listener.message)
        self.process = await create_subprocess_exec(*cmd, stdout=PIPE)
        await status.read_stdout()
        return_code = await self.process.wait()
        if return_code == 0:
            await self.__listener.onDownloadComplete()
        else:
            await self.__listener.onDownloadError("Cancelled by user")
    
    def cancel_download(self):
        self.process.kill()

        