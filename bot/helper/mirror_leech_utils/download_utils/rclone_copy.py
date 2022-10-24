from asyncio import create_subprocess_exec
from asyncio.subprocess import PIPE
from random import SystemRandom
from string import ascii_letters, digits
from bot import status_dict, status_dict_lock
from bot.helper.ext_utils.message_utils import sendStatusMessage
from bot.helper.ext_utils.misc_utils import get_rclone_config
from bot.helper.mirror_leech_utils.status_utils.rclone_status import RcloneStatus
from bot.helper.mirror_leech_utils.status_utils.status_utils import MirrorStatus


class RcloneCopy:
    def __init__(self, user_id, listener= None) -> None:
        self.__listener = listener
        self._user_id= user_id
        self.size= 0
        self.name= ""
        self.err_message= ""
        self.is_user_cancelled= False
        self.process= None
        self.status_type= MirrorStatus.STATUS_COPYING

    async def copy(self, origin_drive, origin_dir, dest_drive, dest_dir):
        conf_path = get_rclone_config(self._user_id)
        cmd = ['rclone', 'copyto', f'--config={conf_path}', f'{origin_drive}:{origin_dir}',
            f'{dest_drive}:{dest_dir}{origin_dir}', '--drive-acknowledge-abuse', '--drive-server-side-across-configs', '-P']
        self.process = await create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
        gid = ''.join(SystemRandom().choices(ascii_letters + digits, k=10))
        async with status_dict_lock:
            status = RcloneStatus(self, gid)
            status_dict[self.__listener.uid] = status
        await sendStatusMessage(self.__listener.message)
        await status.read_stdout()
        return_code = await self.process.wait()
        if return_code == 0:
            await self.__listener.onRcloneCopyComplete(conf_path, origin_dir, dest_drive, dest_dir)
        else:
            if self.is_user_cancelled:
                await self.__listener.onDownloadError(self.err_message)
            else:
                self.err_message = await self.process.stderr.read()
                await self.__listener.onDownloadError(str(self.err_message))
            
    def cancel_download(self):
        self.is_user_cancelled= True
        self.err_message= "Cancelled by user"
        self.process.kill()