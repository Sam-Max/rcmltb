from subprocess import Popen, PIPE
from bot.core.get_vars import get_val
from bot.utils.status_utils.misc_utils import MirrorStatus
from bot.utils.status_utils.rclone_status import RcloneStatus
from bot.utils.bot_utils.misc_utils import get_rclone_config



class RcloneCopy:
    def __init__(self, user_msg) -> None:
        self.__user_msg = user_msg

    async def copy(self):
        await self.__user_msg.edit(text="Starting copy...")
        origin_drive = get_val("ORIGIN_DRIVE")
        origin_dir = get_val("ORIGIN_DIR")
        dest_drive = get_val("DEST_DRIVE")
        dest_dir = get_val("DEST_DIR")

        conf_path = get_rclone_config()
        rclone_copy_cmd = ['rclone', 'copy', f'--config={conf_path}', f'{origin_drive}:{origin_dir}',
                       f'{dest_drive}:{dest_dir}', '-P']

        self.__rclone_pr = Popen(rclone_copy_cmd, stdout=(PIPE),stderr=(PIPE))
        rclone_status= RcloneStatus(self.__rclone_pr, self.__user_msg)
        status= await rclone_status.progress(status_type= MirrorStatus.STATUS_COPYING, client_type='telethon')
        
        if status== False:return
        await self.__user_msg.edit("Copied Successfully ✅")
