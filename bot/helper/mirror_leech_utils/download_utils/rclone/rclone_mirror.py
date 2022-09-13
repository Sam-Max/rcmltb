from configparser import ConfigParser
from os import path as ospath
from subprocess import Popen, PIPE
from bot import LOGGER
from bot.helper.ext_utils.message_utils import editMessage
from bot.helper.ext_utils.misc_utils import ButtonMaker, clean, get_rclone_config, rename_file
from bot.helper.ext_utils.rclone_utils import get_gid
from bot.helper.ext_utils.var_holder import get_rclone_var
from bot.helper.mirror_leech_utils.status_utils.rclone_status import RcloneStatus
from bot.helper.mirror_leech_utils.status_utils.status_utils import MirrorStatus


class RcloneMirror:
    def __init__(self, path, message, tag, user_id, new_name="", is_rename=False):
        self.__path = path
        self.__message = message
        self.__user_id= user_id
        self.__new_name = new_name
        self.__tag = tag
        self.__is_rename = is_rename
        self.__dest_base = get_rclone_var('MIRRORSET_BASE_DIR', self.__user_id)
        self.__dest_drive = get_rclone_var('MIRRORSET_DRIVE', self.__user_id)
        self.__is_gdrive= False

    async def mirror(self):
        conf_path = get_rclone_config(self.__user_id)
        conf = ConfigParser()
        conf.read(conf_path)
        
        for i in conf.sections():
            if self.__dest_drive == str(i):
                if conf[i]['type'] == 'drive':
                    self.__is_gdrive = True
                else:
                    self.__is_gdrive = False
                break
        
        if self.__is_rename:
            self.__path = rename_file(self.__path, self.__new_name)

        if ospath.isdir(self.__path):
            name = ospath.basename(self.__path)
            cmd = ['rclone', 'copy', f"--config={conf_path}", str(self.__path),
                    f"{self.__dest_drive}:{self.__dest_base}/{name}", '-P']
        else:
            cmd = ['rclone', 'copy', f"--config={conf_path}", str(self.__path),
                    f"{self.__dest_drive}:{self.__dest_base}", '-P']

        process = Popen(cmd, stdout=(PIPE), stderr=(PIPE))
        rclone_status= RcloneStatus(process, self.__message, self.__path)
        status= await rclone_status.start(status_type= MirrorStatus.STATUS_UPLOADING)
        if status:
            await self.__onDownloadComplete(conf_path)
        else:
            await self.__onDownloadCancel()  
          
    async def __onDownloadComplete(self, conf_path):   
          button= ButtonMaker() 
          name = ospath.basename(self.__path)
          msg = f"<b>Name: </b><code>{name}</code>"
          if ospath.isdir(self.__path):
                if self.__is_gdrive:
                    gid = await get_gid(self.__dest_drive, self.__dest_base, f"{name}/", conf_path)
                    link = f"https://drive.google.com/folderview?id={gid[0]}"
                    button.url_buildbutton('Drive Link', link)
                    await editMessage(f"{msg}\n\n<b>cc: </b>{self.__tag}", self.__message, button.build_menu(1))
                else:
                    await editMessage(f"{msg}\n\n<b>cc: </b>{self.__tag}", self.__message)     
          else:
                if self.__is_gdrive:
                    gid = await get_gid(self.__dest_drive, self.__dest_base, name, conf_path, False)
                    link = f"https://drive.google.com/file/d/{gid[0]}/view"
                    button.url_buildbutton('Drive Link', link)
                    await editMessage(f"{msg}\n\n<b>cc: </b>{self.__tag}", self.__message, button.build_menu(1))
                else:
                    await editMessage(f"{msg}\n\n<b>cc: </b>{self.__tag}", self.__message)          
          clean(self.__path)

    async def __onDownloadCancel(self):
        await self.__message.edit('Download cancelled')
        clean(self.__path)    