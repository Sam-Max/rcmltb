from asyncio import create_subprocess_exec
from asyncio.subprocess import PIPE
from os import path as ospath
from random import SystemRandom
from string import ascii_letters, digits
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import sendStatusMessage
from bot.helper.ext_utils.rclone_data_holder import get_rclone_data
from bot import status_dict, status_dict_lock, config_dict
from bot.helper.ext_utils.rclone_utils import get_rclone_path, setRcloneFlags
from bot.helper.mirror_leech_utils.status_utils.rclone_status import RcloneStatus
from bot.helper.mirror_leech_utils.status_utils.status_utils import MirrorStatus


class RcloneLeech:
    def __init__(self, origin_dir, dest_dir, listener, isFolder=False):
        self.__listener = listener
        self.__user_id = listener.user_id
        self.__origin_path = origin_dir
        self.__dest_path = dest_dir
        self.__isFolder = isFolder
        self.size = 0
        self.name = None
        self.process = None
        self.__is_cancelled = False
        self.status_type = MirrorStatus.STATUS_DOWNLOADING

    async def leech(self):
        conf_path = await get_rclone_path(self.__user_id, self.__listener.message)
        if config_dict["MULTI_RCLONE_CONFIG"] or CustomFilters._owner_query(
            self.__user_id
        ):
            leech_drive = get_rclone_data("LEECH_REMOTE", self.__user_id)
            cmd = [
                "rclone",
                "copy",
                f"--config={conf_path}",
                f"{leech_drive}:{self.__origin_path}",
                f"{self.__dest_path}",
                "-P",
            ]
        else:
            if DEFAULT_GLOBAL_REMOTE := config_dict["DEFAULT_GLOBAL_REMOTE"]:
                cmd = [
                    "rclone",
                    "copy",
                    f"--config={conf_path}",
                    f"{DEFAULT_GLOBAL_REMOTE}:{self.__origin_path}",
                    f"{self.__dest_path}",
                    "-P",
                ]
            else:
                await self.__listener.onDownloadError("DEFAULT_GLOBAL_REMOTE not found")
                return
        await setRcloneFlags(cmd, "download")
        gid = "".join(SystemRandom().choices(ascii_letters + digits, k=10))
        if self.__isFolder:
            self.name = ospath.basename(ospath.normpath(self.__dest_path))
        else:
            self.name = ospath.basename(self.__dest_path)
        async with status_dict_lock:
            status = RcloneStatus(self, self.__listener, gid)
            status_dict[self.__listener.uid] = status
        await sendStatusMessage(self.__listener.message)
        self.process = await create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
        await status.start()
        return_code = await self.process.wait()
        if self.__is_cancelled:
            return
        if return_code == 0:
            await self.__listener.onDownloadComplete()
        else:
            err_message = (await self.process.stderr.read()).decode()
            await self.__listener.onDownloadError(f"Error: {err_message}!")

    async def cancel_download(self):
        self.__is_cancelled = True
        if self.process is not None:
            try:
                self.process.kill()
            except:
                pass
        await self.__listener.onDownloadError("Download cancelled!")
