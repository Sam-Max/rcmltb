from asyncio import create_subprocess_exec
from asyncio.subprocess import PIPE
from configparser import ConfigParser
from random import SystemRandom
from string import ascii_letters, digits
from bot import LOGGER
from bot.helper.ext_utils.message_utils import editMessage
from bot.helper.ext_utils.misc_utils import ButtonMaker, clean, get_rclone_config
from bot.helper.ext_utils.rclone_utils import get_gid
from bot.helper.ext_utils.var_holder import get_rclone_var
from bot.helper.mirror_leech_utils.status_utils.rclone_status import RcloneStatus
from bot.helper.mirror_leech_utils.status_utils.status_utils import MirrorStatus


class RcloneMirror:
    def __init__(self, path, name, message, tag, user_id, isExtract= False):
        self.__path = path
        self.__name= name
        self.__message = message
        self.__user_id= user_id
        self.__tag = tag
        self.__is_extract= isExtract
        self.__base = get_rclone_var('MIRRORSET_BASE_DIR', self.__user_id)
        self.__drive = get_rclone_var('MIRRORSET_DRIVE', self.__user_id)
        self.__is_gdrive = False

    async def mirror(self):
        conf_path = get_rclone_config(self.__user_id)
        conf = ConfigParser()
        conf.read(conf_path)

        for i in conf.sections():
            if self.__drive == str(i):
                if conf[i]['type'] == 'drive':
                    self.__is_gdrive = True
                    break
        
        cmd = ['rclone', 'copy', f"--config={conf_path}", str(self.__path), f"{self.__drive}:{self.__base}", '-P']
        rc_process = await create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
        gid = ''.join(SystemRandom().choices(ascii_letters + digits, k=10))
        status_type= MirrorStatus.STATUS_UPLOADING
        rclone_status= RcloneStatus(rc_process, self.__message, status_type, gid, self.__name)
        status= await rclone_status.start()
        if status:
            await self.__onDownloadComplete(conf_path)
        else:
            await self.__onDownloadCancel()  
          
    async def __onDownloadComplete(self, conf_path):   
        button= ButtonMaker() 
        msg = f"<b>Name: </b><code>{self.__name}</code>"
        if self.__is_extract:
            if self.__is_gdrive:
                gid = await get_gid(self.__drive, self.__base, f"{self.__name}/", conf_path)
                link = f"https://drive.google.com/folderview?id={gid[0]}"
                button.url_buildbutton('Drive Link', link)
                await editMessage(f"{msg}\n\n<b>cc: </b>{self.__tag}", self.__message, button.build_menu(1))
            else:
                await editMessage(f"{msg}\n\n<b>cc: </b>{self.__tag}", self.__message) 
        else:
            if self.__is_gdrive:
                gid = await get_gid(self.__drive, self.__base, self.__name, conf_path, False)
                link = f"https://drive.google.com/file/d/{gid[0]}/view"
                button.url_buildbutton('Drive Link', link)
                await editMessage(f"{msg}\n\n<b>cc: </b>{self.__tag}", self.__message, button.build_menu(1))
            else:
                await editMessage(f"{msg}\n\n<b>cc: </b>{self.__tag}", self.__message)          
        clean(self.__path)

    async def __onDownloadCancel(self):
        await self.__message.edit('Download cancelled')
        clean(self.__path)    