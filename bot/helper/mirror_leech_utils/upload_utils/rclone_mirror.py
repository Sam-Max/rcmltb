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
from bot.helper.ext_utils.misc_utils import clean_download, count_files_and_folders
from bot.helper.ext_utils.rclone_data_holder import get_rclone_data
from bot.helper.ext_utils.rclone_utils import (
    get_rclone_path,
    is_gdrive_remote,
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
        self.__is_cancelled = False
        self.status_type = MirrorStatus.STATUS_UPLOADING

    async def mirror(self):
        await self.delete_files_with_extensions()

        if ospath.isdir(self.__path):
            mime_type = "Folder"
        else:
            mime_type = "File"

        conf_path = await get_rclone_path(self.__user_id, self.message)
        folder_name = self.name.replace(".", "")
        is_multi_remote_up = config_dict["MULTI_REMOTE_UP"]
        is_sudo_filter = CustomFilters.sudo_filter("", self.message)

        if config_dict["MULTI_RCLONE_CONFIG"] or is_sudo_filter:
            if is_multi_remote_up and len(remotes_multi) > 0:
                for rc_remote in remotes_multi:
                    await self.upload(self.__path, conf_path, mime_type, rc_remote)
                await clean_download(self.__path)
                return

            rc_remote = get_rclone_data("MIRROR_SELECT_REMOTE", self.__user_id)
            base_dir = get_rclone_data("MIRROR_SELECT_BASE_DIR", self.__user_id)

            await self.upload(
                self.__path, conf_path, mime_type, rc_remote, folder_name, base_dir
            )
        else:
            DEFAULT_GLOBAL_REMOTE = config_dict["DEFAULT_GLOBAL_REMOTE"]
            if DEFAULT_GLOBAL_REMOTE:
                await self.upload(
                    self.__path,
                    conf_path,
                    mime_type,
                    DEFAULT_GLOBAL_REMOTE,
                    folder_name,
                )
            else:
                await self.__listener.onUploadError("DEFAULT_GLOBAL_REMOTE not found")
                return

    async def upload(
        self, path, conf_path, mime_type, remote, folder_name, base_dir=""
    ):
        if mime_type == "Folder":
            self.name = folder_name
            if base_dir:
                rclone_path = f"{remote}:{base_dir}{folder_name}"
            else:
                rclone_path = f"{remote}:/{folder_name}"
        else:
            if base_dir:
                rclone_path = f"{remote}:{base_dir}"
            else:
                rclone_path = f"{remote}:/"

        cmd = [
            "rclone",
            "copy",
            f"--config={conf_path}",
            f"{path}",
            rclone_path,
            "-P",
        ]

        is_gdrive = is_gdrive_remote(remote, conf_path)
        await setRcloneFlags(cmd, "upload")

        if ospath.isdir(path):
            folders, files = await count_files_and_folders(path)
        else:
            if path.lower().endswith(tuple(GLOBAL_EXTENSION_FILTER)):
                await self.__listener.onUploadError(
                    "This file extension is excluded by extension filter!"
                )
                return
            folders = 0
            files = 1

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

            await self.__listener.onUploadComplete(
                None,
                size,
                files,
                folders,
                mime_type,
                self.name,
                rclone_config=conf_path,
                rclone_path=rclone_path,
                is_gdrive=is_gdrive,
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

    async def cancel_task(self):
        self.__is_cancelled = True
        if self.process is not None:
            try:
                self.process.kill()
            except:
                pass
        await self.__listener.onUploadError("Upload cancelled!")
