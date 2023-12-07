from asyncio import create_subprocess_exec
from asyncio.subprocess import PIPE
from random import SystemRandom
from os import path as ospath, remove as osremove, walk
from string import ascii_letters, digits
from bot import (
    GLOBAL_EXTENSION_FILTER,
    status_dict,
    status_dict_lock,
    remotes_multi,
    config_dict,
)
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.ext_utils.human_format import get_readable_file_size
from bot.helper.telegram_helper.message_utils import sendStatusMessage
from bot.helper.ext_utils.misc_utils import clean_download
from bot.helper.ext_utils.rclone_data_holder import get_rclone_data
from bot.helper.ext_utils.rclone_utils import (
    gdrive_check,
    get_rclone_path,
    setRcloneFlags,
)
from bot.helper.mirror_leech_utils.status_utils.rclone_status import RcloneStatus
from bot.helper.mirror_leech_utils.status_utils.status_utils import MirrorStatus


class RcloneMirror:
    def __init__(self, path, name, size, user_id, listener):
        self.__path = path
        self.__listener = listener
        self.message = self.__listener.message
        self.__user_id = user_id
        self.name = name
        self.size = size
        self.process = None
        self.__isGdrive = False
        self.__is_cancelled = False
        self.status_type = MirrorStatus.STATUS_UPLOADING

    async def mirror(self):
        await self.delete_files_with_extensions()

        if self.__listener.extract:
            mime_type = "Folder"
        else:
            mime_type = "File"

        conf_path = await get_rclone_path(self.__user_id, self.message)
        is_multi_remote_up = config_dict["MULTI_REMOTE_UP"]
        is_owner_query = CustomFilters._owner_query(self.__user_id)
        foldername = self.name.replace(".", "")

        if config_dict["MULTI_RCLONE_CONFIG"] or is_owner_query:
            if is_multi_remote_up and len(remotes_multi) > 0:
                for remote in remotes_multi:
                    self.__isGdrive = await gdrive_check(remote, conf_path)
                    if mime_type == "Folder":
                        cmd = [
                            "rclone",
                            "copy",
                            f"--config={conf_path}",
                            str(self.__path),
                            f"{remote}:/{foldername}",
                            "-P",
                        ]
                    else:
                        cmd = [
                            "rclone",
                            "copy",
                            f"--config={conf_path}",
                            str(self.__path),
                            f"{remote}:",
                            "-P",
                        ]
                    await setRcloneFlags(cmd, "upload")
                    await self.upload(cmd, conf_path, mime_type, remote)
                await clean_download(self.__path)
            else:
                remote = get_rclone_data("MIRROR_SELECT_REMOTE", self.__user_id)
                base = get_rclone_data("MIRROR_SELECT_BASE_DIR", self.__user_id)
                self.__isGdrive = await gdrive_check(remote, conf_path)

                if mime_type == "Folder":
                    cmd = [
                        "rclone",
                        "copy",
                        f"--config={conf_path}",
                        str(self.__path),
                        f"{remote}:{base}{foldername}",
                        "-P",
                    ]
                else:
                    cmd = [
                        "rclone",
                        "copy",
                        f"--config={conf_path}",
                        str(self.__path),
                        f"{remote}:{base}",
                        "-P",
                    ]
                await setRcloneFlags(cmd, "upload")
                await self.upload(cmd, conf_path, mime_type, remote, base)
        else:
            if DEFAULT_GLOBAL_REMOTE := config_dict["DEFAULT_GLOBAL_REMOTE"]:
                self.__isGdrive = await gdrive_check(DEFAULT_GLOBAL_REMOTE, conf_path)

                if mime_type == "Folder":
                    cmd = [
                        "rclone",
                        "copy",
                        f"--config={conf_path}",
                        str(self.__path),
                        f"{DEFAULT_GLOBAL_REMOTE}:/{foldername}",
                        "-P",
                    ]
                else:
                    cmd = [
                        "rclone",
                        "copy",
                        f"--config={conf_path}",
                        str(self.__path),
                        f"{DEFAULT_GLOBAL_REMOTE}:",
                        "-P",
                    ]
                await setRcloneFlags(cmd, "upload")
                await self.upload(cmd, conf_path, mime_type, DEFAULT_GLOBAL_REMOTE)
            else:
                await self.__listener.onUploadError("DEFAULT_GLOBAL_REMOTE not found")
                return

    async def upload(self, cmd, config_file, mime_type, remote, base="/"):
        gid = "".join(SystemRandom().choices(ascii_letters + digits, k=10))
        async with status_dict_lock:
            status = RcloneStatus(self, self.__listener, gid)
            status_dict[self.__listener.uid] = status
        await sendStatusMessage(self.message)
        self.process = await create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
        await status.start()
        return_code = await self.process.wait()
        if self.__is_cancelled:
            return
        if return_code == 0:
            size = get_readable_file_size(self.size)
            await self.__listener.onRcloneUploadComplete(
                self.name, size, config_file, remote, base, mime_type, self.__isGdrive
            )
        else:
            error = (await self.process.stderr.read()).decode().strip()
            await self.__listener.onUploadError(f"Error: {error}!")

    async def delete_files_with_extensions(self):
        for dirpath, _, files in walk(self.__path):
            for file in files:
                if file.lower().endswith(tuple(GLOBAL_EXTENSION_FILTER)):
                    try:
                        del_file = ospath.join(dirpath, file)
                        osremove(del_file)
                    except:
                        return

    async def cancel_download(self):
        self.__is_cancelled = True
        if self.process is not None:
            try:
                self.process.kill()
            except:
                pass
        await self.__listener.onUploadError("Upload cancelled!")
