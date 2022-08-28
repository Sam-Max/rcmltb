#Modified from: https://github.com/5MysterySD/Tele-LeechX

from asyncio import create_subprocess_exec
from asyncio.subprocess import PIPE
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from bot.core.varholderwrap import get_val
from bot.utils.bot_utils.bot_utils import is_gdrive_link
from bot.utils.bot_utils.message_utils import editMessage,sendMessage
from bot import LOGGER
from re import search, escape
from urllib.parse import parse_qs, urlparse
from bot.utils.status_utils.clone_status import CloneStatus
from bot.utils.status_utils.status_utils import MirrorStatus, TelegramClient


class GDriveClone:
    def __init__(self, message, text):
        self.text= text
        self.link= ""
        self.link_id = ""
        self.message = message
        self.user_id= self.message.from_user.id
        self.user_mention = self.message.from_user.mention
        self.edit_msg= ""
        self.name = ""
        self.file_name= ""
        self.drive_name = get_val("RCLONE_DRIVE")
        self.base_dir= get_val("MIRRORSET_BASE_DIR")

    async def execute(self):
        args = self.text.split("|", maxsplit=1)
        if len(args) > 1:
            self.link = args[0].strip()
            self.name = args[1].strip()
            if is_gdrive_link(self.link):
                self.link_id = self.getIdFromUrl(self.link)
            else:
                return await sendMessage("Not a Gdrive link", self.message)
        else:
            self.link = self.text
            self.name = "" 
            if is_gdrive_link(self.link):
                self.link_id = self.getIdFromUrl(self.link)
            else:
                return await sendMessage("Not a Gdrive link", self.message)

        self.edit_msg = await sendMessage("Cloning Started...", self.message)
        id = "{"f"{self.link_id}""}"
        cmd = ["gclone", "copy", "--config=rclone.conf", f"{self.drive_name}:{id}",
              f"{self.drive_name}:{self.base_dir}{self.name}", "-v", "--drive-server-side-across-configs", 
              "--transfers=16", "--checkers=20",]
        process = await create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
        rclone_status= CloneStatus(process, self.edit_msg, self.name)
        status, file_name = await rclone_status.progress(status_type=MirrorStatus.STATUS_CLONING, 
                client_type=TelegramClient.PYROGRAM)
        if status:
            await self.__onCloningComplete(file_name)

    async def __onCloningComplete(self, file_name):    
            if file_name:
                self.name= file_name
                _type = "File"
                _flag = "--files-only"
                _dir= ""
            
            if self.name:
                _flag = "--dirs-only"
                _type = "Folder"
                _dir= "/"

            g_name= escape(self.name)
            with open("filter.txt", "w+", encoding="utf-8") as filter:
                 print(f"+ {g_name}{_dir}\n- *", file= filter)

            cmd = ["rclone", "lsf", "--config=./rclone.conf", "-F", "i", "--filter-from=./filter.txt", 
                    f"{_flag}", f"{self.drive_name}:{self.base_dir}"]

            process = await create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
            out, err = await process.communicate()
            out = out.decode("utf-8")
            LOGGER.info(err.decode("utf-8"))

            if _type == "Folder":
                link = f"https://drive.google.com/folderview?id={out}"
            else:
                link = f"https://drive.google.com/file/d/{out}/view?usp=drivesdk"

            url = search(r"(?P<url>https?://[^\s]+)", link).group("url")

            #Calculate Size
            cmd = ["rclone", "size", "--config=rclone.conf", f"{self.drive_name}:{self.base_dir}{self.name}"]
            process = await create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
            out, err = await process.communicate()
            output = out.decode("utf-8")
            
            button = []
            button.append([InlineKeyboardButton(text="GDrive Link", url=f"{url}")])
            format_out = output.replace("Total objects:", "**Total Files** :").replace("Total size:", "**Total Size** :")
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

