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
        self.__is_gdrive = False
        self.__is_cancelled = False
        self.status_type = MirrorStatus.STATUS_UPLOADING

    async def mirror(self):
        await self.delete_files_with_extensions()

        if ospath.isdir(self.__path):
            mime_type = "Folder"
        else:
            mime_type = "File"

        conf_path = await get_rclone_path(self.__user_id, self.message)
        is_multi_remote_up = config_dict["MULTI_REMOTE_UP"]
        is_sudo_filter = CustomFilters.sudo_filter("", self.message)
        foldername = self.name.replace(".", "")

        if config_dict["MULTI_RCLONE_CONFIG"] or is_sudo_filter:
            if is_multi_remote_up and len(remotes_multi) > 0:
                for remote in remotes_multi:
                    self.__is_gdrive = await gdrive_check(remote, conf_path)
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
                    await self.upload(self.__path, cmd, conf_path, mime_type, remote)
                await clean_download(self.__path)
            else:
                remote = get_rclone_data("MIRROR_SELECT_REMOTE", self.__user_id)
                base_dir = get_rclone_data("MIRROR_SELECT_BASE_DIR", self.__user_id)
                self.__is_gdrive = await gdrive_check(remote, conf_path)

                if mime_type == "Folder":
                    cmd = [
                        "rclone",
                        "copy",
                        f"--config={conf_path}",
                        str(self.__path),
                        f"{remote}:{base_dir}{foldername}",
                        "-P",
                    ]
                else:
                    cmd = [
                        "rclone",
                        "copy",
                        f"--config={conf_path}",
                        str(self.__path),
                        f"{remote}:{base_dir}",
                        "-P",
                    ]
                await setRcloneFlags(cmd, "upload")
                await self.upload(
                    self.__path, cmd, conf_path, mime_type, remote, base_dir
                )
        else:
            if DEFAULT_GLOBAL_REMOTE := config_dict["DEFAULT_GLOBAL_REMOTE"]:
                self.__is_gdrive = await gdrive_check(DEFAULT_GLOBAL_REMOTE, conf_path)

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
                await self.upload(
                    self.__path, cmd, conf_path, mime_type, DEFAULT_GLOBAL_REMOTE
                )
            else:
                await self.__listener.onUploadError("DEFAULT_GLOBAL_REMOTE not found")
                return

    async def upload(self, path, cmd, conf_path, mime_type, remote, base_dir="/"):
        if ospath.isdir(path):
            folders, files = await count_files_and_folders(path)
        else:
            if self.__path.lower().endswith(tuple(self.extension_filter)):
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
            rclone_path= f'{remote}:{base_dir}/{self.name}'
            await self.__listener.onUploadComplete(
                None,
                size,
                files,
                folders,
                mime_type,
                self.name,
                rclone_config= conf_path,
                rclone_path= rclone_path,
                is_gdrive= self.__is_gdrive,
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
