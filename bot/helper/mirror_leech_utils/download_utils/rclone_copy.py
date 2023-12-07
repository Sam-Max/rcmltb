from asyncio import create_subprocess_exec
from asyncio.subprocess import PIPE
from configparser import ConfigParser
from os import listdir, path as ospath
from random import SystemRandom, randrange
from string import ascii_letters, digits
from bot import LOGGER, status_dict, status_dict_lock, config_dict
from bot.helper.telegram_helper.message_utils import sendStatusMessage
from bot.helper.ext_utils.rclone_utils import (
    gdrive_check,
    get_rclone_path,
    setRcloneFlags,
)
from bot.helper.mirror_leech_utils.status_utils.rclone_status import RcloneStatus
from bot.helper.mirror_leech_utils.status_utils.status_utils import MirrorStatus


class RcloneCopy:
    def __init__(self, user_id, listener) -> None:
        self.__listener = listener
        self._user_id = user_id
        self.message = self.__listener.message
        self.name = ""
        self.sa_error = ""
        self.size = 0
        self.__sa_count = 0
        self.__sa_number = 0
        self.__service_account_index = 0
        self.process = None
        self.__isGdrive = False
        self.__is_cancelled = False
        self.status_type = MirrorStatus.STATUS_COPYING

    async def copy(self, origin_remote, origin_dir, dest_remote, dest_dir):
        conf_path = await get_rclone_path(self._user_id, self.message)
        self.__isGdrive = await gdrive_check(dest_remote, conf_path)

        if config_dict["USE_SERVICE_ACCOUNTS"] and ospath.exists("accounts"):
            self.__sa_number = len(listdir("accounts"))
            if self.__sa_count == 0:
                self.__service_account_index = randrange(self.__sa_number)
            config = ConfigParser()
            config.read(conf_path)
            if SERVICE_ACCOUNTS_REMOTE := config_dict["SERVICE_ACCOUNTS_REMOTE"]:
                if SERVICE_ACCOUNTS_REMOTE in config.sections():
                    if id := config[SERVICE_ACCOUNTS_REMOTE]["team_drive"]:
                        self.__create_teamdrive_sa_config(conf_path, id)
                        LOGGER.info(
                            f"Using service account remote {SERVICE_ACCOUNTS_REMOTE}"
                        )
                else:
                    LOGGER.info("No remote found on your rclone.conf")
            else:
                LOGGER.info("No SERVICE_ACCOUNTS_REMOTE found")

        cmd = [
            "rclone",
            "copy",
            f"--config={conf_path}",
            "--ignore-case",
            f"{origin_remote}:{origin_dir}",
            f"{dest_remote}:{dest_dir}{origin_dir}",
            "--drive-acknowledge-abuse",
            "-P",
        ]

        await setRcloneFlags(cmd, "copy")

        self.process = await create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)

        self.name = f"{origin_remote}:{origin_dir}"
        gid = "".join(SystemRandom().choices(ascii_letters + digits, k=10))

        async with status_dict_lock:
            status = RcloneStatus(self, self.__listener, gid)
            status_dict[self.__listener.uid] = status
        await sendStatusMessage(self.message)
        await status.start()

        return_code = await self.process.wait()

        if self.__is_cancelled:
            return

        if return_code == 0:
            await self.__listener.onRcloneCopyComplete(
                conf_path, origin_dir, dest_remote, dest_dir, self.__isGdrive
            )
        else:
            err = (await self.process.stderr.read()).decode().strip()
            LOGGER.info(f"Error: {err}")
            if config_dict["USE_SERVICE_ACCOUNTS"] and "RATE_LIMIT_EXCEEDED" in err:
                if self.__sa_number != 0 and self.__sa_count < self.__sa_number:
                    self.__switchServiceAccount()
                    await self.copy(origin_remote, origin_dir, dest_remote, dest_dir)
                    return
                else:
                    LOGGER.info(f"Reached maximum number of service accounts")
            await self.__listener.onDownloadError(err)

    def __switchServiceAccount(self):
        if self.__service_account_index == self.__sa_number - 1:
            self.__service_account_index = 0
        else:
            self.__service_account_index += 1
        self.__sa_count += 1
        LOGGER.info(f"Switching to {self.__service_account_index}.json service account")

    def __create_teamdrive_sa_config(self, conf_path, id):
        rc_content = "type = drive\n"
        rc_content += "scope = drive\n"
        rc_content += (
            f"service_account_file = accounts/{self.__service_account_index}.json\n"
        )
        rc_content += f"team_drive = {id}\n\n"
        with open(conf_path, "w") as f:
            f.write(rc_content)

    async def cancel_download(self):
        self.__is_cancelled = True
        if self.process is not None:
            try:
                self.process.kill()
            except:
                pass
        await self.__listener.onDownloadError("Copy cancelled!")
