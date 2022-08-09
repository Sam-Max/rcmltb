from subprocess import Popen, PIPE
from bot.core.get_vars import get_val
from bot.utils.status_utils.misc_utils import MirrorStatus, TelegramClient
from bot.utils.status_utils.rclone_status import RcloneStatus
from bot.utils.bot_utils.misc_utils import get_rclone_config


class RcloneCopy:
    def __init__(self, user_msg) -> None:
        self.__user_msg = user_msg
        self.__rclone_pr= None

    async def copy(self):
        await self.__user_msg.edit(text="Starting copy...")
        origin_drive = get_val("ORIGIN_DRIVE")
        origin_dir = get_val("ORIGIN_DIR")
        dest_drive = get_val("DEST_DRIVE")
        dest_dir = get_val("DEST_DIR")

        conf_path = get_rclone_config()
        cmd = ['rclone', 'copy', f'--config={conf_path}', f'{origin_drive}:{origin_dir}',
                       f'{dest_drive}:{dest_dir}', '-P']

        self.__rclone_pr = Popen(cmd, stdout=(PIPE),stderr=(PIPE))
        rc_status= RcloneStatus(self.__rclone_pr, self.__user_msg)
        status= await rc_status.progress(
                            status_type= MirrorStatus.STATUS_COPYING, 
                            client_type=TelegramClient.TELETHON)
        if status == True:
             await self.__user_msg.edit("Copied Successfully!!")
