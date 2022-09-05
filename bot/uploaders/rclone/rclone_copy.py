from asyncio import create_subprocess_exec as exec
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from re import search
from subprocess import Popen, PIPE
from bot.utils.var_holder import get_rclone_var
from bot.utils.bot_utils.drive_utils import get_gid
from bot.utils.bot_utils.message_utils import editMessage
from bot.utils.status_utils.status_utils import MirrorStatus, TelegramClient
from bot.utils.status_utils.rclone_status import RcloneStatus
from bot.utils.bot_utils.misc_utils import get_rclone_config


class RcloneCopy:
    def __init__(self, message, user_id) -> None:
        self.__message = message
        self._user_id= user_id
        self.__rclone_pr= None

    async def copy(self):
        conf_path = get_rclone_config(self._user_id)
        await editMessage("Starting Download", self.__message)
        origin_drive = get_rclone_var("COPY_ORIGIN_DRIVE", self._user_id)
        origin_dir = get_rclone_var("COPY_ORIGIN_DIR", self._user_id)
        dest_drive = get_rclone_var("COPY_DESTINATION_DRIVE", self._user_id)
        dest_dir = get_rclone_var("COPY_DESTINATION_DIR", self._user_id)

        cmd = ['rclone', 'copy', f'--config={conf_path}', f'{origin_drive}:{origin_dir}',
                       f'{dest_drive}:{dest_dir + origin_dir}', '-P']

        self.__rclone_pr = Popen(cmd, stdout=(PIPE),stderr=(PIPE))
        rc_status= RcloneStatus(self.__rclone_pr, self.__message)
        status= await rc_status.progress(status_type= MirrorStatus.STATUS_COPYING, 
                            client_type=TelegramClient.PYROGRAM)
        if status:
            gid = await get_gid(dest_drive, dest_dir, origin_dir, conf_path)
            folder_link = f"https://drive.google.com/folderview?id={gid[0]}"
            url = search(r"(?P<url>https?://[^\s]+)", folder_link).group("url")
           
            #Calculate Size
            cmd = ["rclone", "size", "--config=rclone.conf", f"{dest_drive}:{dest_dir}{origin_dir}"]
            process = await exec(*cmd, stdout=PIPE, stderr=PIPE)
            out, _ = await process.communicate()
            output = out.decode("utf-8")

            button = []
            button.append([InlineKeyboardButton(text="GDrive Link", url=f"{url}")])
            format_out = output.replace("Total objects:", "**Total Files** :").replace("Total size:", "**Total Size** :")
            await editMessage(f"{format_out}", self.__message, reply_markup= InlineKeyboardMarkup(button))
        else:
            await editMessage("Copy Cancelled", self.__message)    
