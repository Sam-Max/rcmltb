from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from re import search
from subprocess import Popen, PIPE
from bot.core.varholderwrap import get_val
from bot.utils.bot_utils.drive_utils import get_gid
from bot.utils.bot_utils.message_utils import editMessage
from bot.utils.status_utils.status_utils import MirrorStatus, TelegramClient
from bot.utils.status_utils.rclone_status import RcloneStatus
from bot.utils.bot_utils.misc_utils import get_rclone_config


class RcloneCopy:
    def __init__(self, user_msg) -> None:
        self.__message = user_msg
        self.__rclone_pr= None

    async def execute(self):
        conf_path = get_rclone_config()
        await editMessage("Starting copy...", self.__message)
        origin_drive = get_val("ORIGIN_DRIVE")
        origin_dir = get_val("ORIGIN_DIR")
        dest_drive = get_val("DESTINATION_DRIVE")
        dest_dir = get_val("DESTINATION_DIR")

        cmd = ['rclone', 'copy', f'--config={conf_path}', f'{origin_drive}:{origin_dir}',
                       f'{dest_drive}:{dest_dir + origin_dir}', '-P']

        self.__rclone_pr = Popen(cmd, stdout=(PIPE),stderr=(PIPE))
        rc_status= RcloneStatus(self.__rclone_pr, self.__message)
        status= await rc_status.progress(
                            status_type= MirrorStatus.STATUS_COPYING, 
                            client_type=TelegramClient.TELETHON)
        if status:
            gid = await get_gid(dest_drive, dest_dir, origin_dir, conf_path)
            folder_link = f"https://drive.google.com/folderview?id={gid[0]}"
            url = search(r"(?P<url>https?://[^\s]+)", folder_link).group("url")
            button = []
            button.append([InlineKeyboardButton(text="GDrive Link", url=f"{url}")])
            msg = "Copy Completed.\n"
            msg += f"**Total Files** : N/A\n"
            await editMessage(msg, self.__message, reply_markup= InlineKeyboardMarkup(button))
        else:
             await editMessage("Copy Cancelled", self.__message)    
