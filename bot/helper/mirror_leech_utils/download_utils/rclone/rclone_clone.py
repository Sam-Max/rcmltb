#Modified from: https://github.com/5MysterySD/Tele-LeechX

from asyncio import create_subprocess_exec as exec
from asyncio.subprocess import PIPE
import json
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from bot import LOGGER
from re import search, escape
from urllib.parse import parse_qs, urlparse
from bot.helper.ext_utils.human_format import human_readable_bytes
from bot.helper.ext_utils.message_utils import editMessage, sendMessage
from bot.helper.ext_utils.misc_utils import get_rclone_config
from bot.helper.ext_utils.var_holder import get_rclone_var
from bot.helper.mirror_leech_utils.status_utils.clone_status import CloneStatus
from bot.helper.mirror_leech_utils.status_utils.status_utils import MirrorStatus, TelegramClient


class GDriveClone:
    def __init__(self, message, user_id, link, name):
        self.link= link
        self.message = message
        self.user_id= user_id
        self.edit_msg= ""
        self.name = name
        self.link_id = ""
        self.file_name= ""
        self.conf_path= ""
        self.drive_name = get_rclone_var("MIRRORSET_DRIVE", self.user_id)
        self.base_dir= get_rclone_var("MIRRORSET_BASE_DIR", self.user_id)

    async def clone(self):
        self.conf_path = get_rclone_config(self.user_id)
        self.link_id = self.getIdFromUrl(self.link)
        self.edit_msg = await sendMessage("Cloning Started...", self.message)
        id = "{"f"{self.link_id}""}"
        cmd = ["gclone", "copy", f'--config={self.conf_path}', f"{self.drive_name}:{id}",
              f"{self.drive_name}:{self.base_dir}{self.name}", "-v", "--drive-server-side-across-configs", 
              "--transfers=16", "--checkers=20",]
        process = await exec(*cmd, stdout=PIPE, stderr=PIPE)
        rclone_status= CloneStatus(process, self.edit_msg, self.name)
        status, file_name = await rclone_status.progress(status_type=MirrorStatus.STATUS_CLONING)
        if status:
            await self.__onCloningComplete(file_name)

    async def __onCloningComplete(self, file_name):    
            if len(file_name) > 0:
                self.name= file_name
                _type = "File"
                _flag = "--files-only"
                _dir= ""
            
            if len(self.name) > 0:
                _flag = "--dirs-only"
                _type = "Folder"
                _dir= "/"

            g_name= escape(self.name)
            with open("filter.txt", "w+", encoding="utf-8") as filter:
                 print(f"+ {g_name}{_dir}\n- *", file=filter)

            cmd = ["rclone", "lsf", f'--config={self.conf_path}', "-F", "i", "--filter-from=./filter.txt", 
                    f"{_flag}", f"{self.drive_name}:{self.base_dir}"]

            process = await exec(*cmd, stdout=PIPE, stderr=PIPE)
            out, err = await process.communicate()
            out = out.decode("utf-8")

            if _type == "Folder":
                link = f"https://drive.google.com/folderview?id={out}"
            else:
                link = f"https://drive.google.com/file/d/{out}/view?usp=drivesdk"

            url = search(r"(?P<url>https?://[^\s]+)", link).group("url")

            #Calculate Size
            cmd = ["rclone", "size", f'--config={self.conf_path}', "--json", f"{self.drive_name}:{self.base_dir}{self.name}"]
            process = await exec(*cmd, stdout=PIPE, stderr=PIPE)
            out, err = await process.communicate()
            output = out.decode().strip()
            data = json.loads(output)
            files = data["count"]
            bytes = data["bytes"]
            
            button = []
            button.append([InlineKeyboardButton(text="GDrive Link", url=f"{url}")])
            format_out = f"**Total Files** {files}\n" 
            format_out += f"**Total Size**: {human_readable_bytes(bytes) }"
            msg = f"**Name** : `{self.name}`\n\n"
            msg += f"**Type** : {_type}\n"
            msg += f"{format_out}\n"
            await editMessage(msg, self.edit_msg, reply_markup= InlineKeyboardMarkup(button))

    @staticmethod
    def getIdFromUrl(link: str):
        if "folders" in link or "file" in link:
            regex = r"https:\/\/drive\.google\.com\/(?:drive(.*?)\/folders\/|file(.*?)?\/d\/)([-\w]+)"
            res = search(regex, link)
            if res is None:
                LOGGER.info("G-Drive ID not found.")
            return res.group(3)
        parsed = urlparse(link)
        return parse_qs(parsed.query)['id'][0]

