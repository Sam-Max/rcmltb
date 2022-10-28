from asyncio import create_subprocess_exec
from asyncio.subprocess import PIPE
from configparser import ConfigParser
from random import SystemRandom
from string import ascii_letters, digits
from bot import LOGGER, status_dict, status_dict_lock
from bot.helper.ext_utils.human_format import get_readable_file_size
from bot.helper.ext_utils.message_utils import sendStatusMessage
from bot.helper.ext_utils.misc_utils import get_rclone_config
from bot.helper.ext_utils.var_holder import get_rclone_val
from bot.helper.mirror_leech_utils.status_utils.rclone_status import RcloneStatus
from bot.helper.mirror_leech_utils.status_utils.status_utils import MirrorStatus


class RcloneMirror:
    def __init__(self, path, name, size, user_id, listener= None):
        self.__path = path
        self.__listener = listener
        self.__user_id= user_id
        self.name= name
        self.size= size
        self.process= None
        self.status_type = MirrorStatus.STATUS_UPLOADING
        self.__isGdrive = False

    async def mirror(self):
        base_dir = get_rclone_val('MIRRORSET_BASE_DIR', self.__user_id)
        drive = get_rclone_val('MIRRORSET_DRIVE', self.__user_id)
        conf_path = get_rclone_config(self.__user_id)
        conf = ConfigParser()
        conf.read(conf_path)
        for i in conf.sections():
            if drive == str(i):
                if conf[i]['type'] == 'drive':
                    self.__isGdrive = True
                    break
        cmd = ['rclone', 'copy', f"--config={conf_path}", str(self.__path), f"{drive}:{base_dir}", '-P']
        gid = ''.join(SystemRandom().choices(ascii_letters + digits, k=10))
        async with status_dict_lock:
            status = RcloneStatus(self, gid)
            status_dict[self.__listener.uid] = status
        await sendStatusMessage(self.__listener.message)
        self.process = await create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
        await status.read_stdout()
        return_code = await self.process.wait()
        if return_code == 0:
            size = get_readable_file_size(self.size)
            await self.__listener.onRcloneUploadComplete(self.name, size, conf_path, drive, base_dir, self.__isGdrive)
        else:
            await self.__listener.onUploadError("Cancelled by user")

    def cancel_download(self):
        self.process.kill()
        