from asyncio import create_subprocess_exec
from asyncio.subprocess import PIPE
from configparser import ConfigParser
from os import listdir, path as ospath
from random import SystemRandom, randrange
from string import ascii_letters, digits
from bot import LOGGER, status_dict, status_dict_lock, config_dict
from bot.helper.ext_utils.message_utils import sendMessage, sendStatusMessage
from bot.helper.ext_utils.rclone_utils import get_rclone_config
from bot.helper.mirror_leech_utils.status_utils.rclone_status import RcloneStatus
from bot.helper.mirror_leech_utils.status_utils.status_utils import MirrorStatus

SERVICE_ACCOUNTS_NUMBER = 100


class RcloneCopy:
    def __init__(self, user_id, listener= None) -> None:
        self.__listener = listener
        self._user_id= user_id
        self.name= None
        self.process= None
        self.size= 0
        self.__sa_count = 0
        self.__service_account_index = 0
        self.__is_cancelled= False
        self.sa_error= ""
        self.status_type= MirrorStatus.STATUS_COPYING

    async def copy(self, origin_drive, origin_dir, dest_drive, dest_dir):
        conf_path = get_rclone_config(self._user_id)
        if config_dict['USE_SERVICE_ACCOUNTS']:
            if ospath.exists("accounts"):
                globals()['SERVICE_ACCOUNTS_NUMBER'] = len(listdir("accounts"))
                if self.__sa_count == 0:
                    self.__service_account_index = randrange(SERVICE_ACCOUNTS_NUMBER)
                config = ConfigParser()
                config.read(conf_path)
                if SERVICE_ACCOUNTS_REMOTE:= config_dict['SERVICE_ACCOUNTS_REMOTE']:
                    if SERVICE_ACCOUNTS_REMOTE in config:
                        if len(config[SERVICE_ACCOUNTS_REMOTE]['team_drive']) > 0:
                            self.__create_teamdrive_sa_config(config, SERVICE_ACCOUNTS_REMOTE)
                        else:
                            return await sendMessage(f"No id found on team_drive field", self.__listener.message)    
                    else:
                        return await sendMessage(f"Not remote found with name: {SERVICE_ACCOUNTS_REMOTE}", self.__listener.message)
                    with open(conf_path, 'w') as configfile:
                        config.write(configfile)
                else:
                    return await sendMessage("You need to set SERVICE_ACCOUNTS_REMOTE variable", self.__listener.message)
        if config_dict['SERVER_SIDE']:
            cmd = ['rclone', 'copy', f'--config={conf_path}', f'{origin_drive}:{origin_dir}',
            f'{dest_drive}:{dest_dir}{origin_dir}', '--drive-acknowledge-abuse', '--drive-server-side-across-configs', '-P']
        else:
            cmd = ['rclone', 'copy', f'--config={conf_path}', f'{origin_drive}:{origin_dir}',
            f'{dest_drive}:{dest_dir}{origin_dir}', '--drive-acknowledge-abuse', '-P']
        self.process = await create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
        gid = ''.join(SystemRandom().choices(ascii_letters + digits, k=10))
        self.name = f'{origin_drive}:{origin_dir} ➡️ {dest_drive}:{dest_dir}'
        async with status_dict_lock:
            status = RcloneStatus(self, self.__listener, gid)
            status_dict[self.__listener.uid] = status
        await sendStatusMessage(self.__listener.message)
        await status.read_stdout()
        return_code = await self.process.wait()
        if self.__is_cancelled:
            return
        if return_code == 0:
            await self.__listener.onRcloneCopyComplete(conf_path, origin_dir, dest_drive, dest_dir)
        else:
            err_message = await self.process.stderr.read()
            err_message= err_message.decode()
            LOGGER.info(f'Error: {err_message}')
            if any(i in err_message for i in ['userRateLimitExceeded', 'User rate limit exceeded.']):
                self.__switchServiceAccount()
                return await self.copy(origin_drive, origin_dir, dest_drive, dest_dir)
            await self.__listener.onDownloadError(err_message)
                
    def __switchServiceAccount(self):
        if self.__service_account_index == SERVICE_ACCOUNTS_NUMBER - 1:
            self.__service_account_index = 0
        else:
            self.__service_account_index += 1
        self.__sa_count += 1
        LOGGER.info(f"Switching to {self.__service_account_index}.json service account")

    def __create_teamdrive_sa_config(self, config, remote):
        config[remote].update({
            'type': 'drive',
            'scope': 'drive',
            'client_id': '',
            'client_secret': '',
            'token': '',
            'service_account_file': f'accounts/{self.__service_account_index}.json',
            'stop_on_upload_limit': 'true',
        })

    async def cancel_download(self):
        self.__is_cancelled= True
        await self.__listener.onDownloadError("Copy cancelled!")
        self.process.kill() 