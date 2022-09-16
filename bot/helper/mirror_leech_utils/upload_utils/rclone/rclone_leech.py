from subprocess import Popen, PIPE
from bot.helper.ext_utils.message_utils import editMessage
from bot.helper.ext_utils.misc_utils import clean, get_rclone_config
from bot.helper.ext_utils.var_holder import get_rclone_var
from bot.helper.mirror_leech_utils.status_utils.rclone_status import RcloneStatus
from bot.helper.mirror_leech_utils.status_utils.status_utils import MirrorStatus
from bot.helper.mirror_leech_utils.mirror_leech import MirrorLeech

class RcloneLeech:
    def __init__(self, message, user_id, origin_dir, dest_dir, isZip=False, extract=False, pswd=None, tag=None, isFolder= False):
        self.__message = message
        self.id = self.__message.id
        self._user_id= user_id
        self.__is_Zip = isZip
        self.__extract = extract
        self.__origin_path = origin_dir
        self.__dest_path = dest_dir
        self.__pswd = pswd
        self.__tag = tag
        self.__isFolder= isFolder

    async def leech(self):
        conf_path = get_rclone_config(self._user_id)
        leech_drive = get_rclone_var("LEECH_DRIVE", self._user_id)
        cmd = ['rclone', 'copy', f'--config={conf_path}', f'{leech_drive}:{self.__origin_path}', 
              f'{self.__dest_path}', '-P']
        process = Popen(cmd, stdout=(PIPE),stderr=(PIPE))
        if self.__isFolder:
            name = self.__dest_path.rsplit("/", 2)[1]
        else:
            name= self.__dest_path.rsplit("/", 1)[1]
        rclone_status= RcloneStatus(process, self.__message, name)
        status= await rclone_status.start(MirrorStatus.STATUS_DOWNLOADING)
        if status:
            await self.__onDownloadComplete()
        else:
            await self.__onDownloadCancel()  

    async def __onDownloadComplete(self):
        if str(self.__dest_path).endswith("/"):
            self.__dest_path= self.__dest_path.rstrip("/")
        ml= MirrorLeech(self.__dest_path, self.__message, self.__tag, self._user_id, isZip=self.__is_Zip, extract=self.__extract, isLeech=True)
        await ml.execute()
    
    async def __onDownloadCancel(self):
        await editMessage('Download cancelled', self.__message )
        clean(self.__dest_path)