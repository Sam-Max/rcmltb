from asyncio import create_subprocess_exec as exec
import asyncio
from json import loads
from random import SystemRandom
from string import ascii_letters, digits
from bot import LOGGER
from bot.helper.ext_utils.human_format import human_readable_bytes
from bot.helper.ext_utils.message_utils import editMessage
from bot.helper.ext_utils.misc_utils import ButtonMaker, get_rclone_config
from bot.helper.mirror_leech_utils.status_utils.rclone_status import RcloneStatus
from bot.helper.mirror_leech_utils.status_utils.status_utils import MirrorStatus


class RcloneCopy:
    def __init__(self, message, user_id) -> None:
        self.__message = message
        self._user_id= user_id

    async def copy(self, origin_drive, origin_dir, dest_drive, dest_dir):
        conf_path = get_rclone_config(self._user_id)
        button= ButtonMaker()
        cmd = ['rclone', 'copy', f'--config={conf_path}', f'{origin_drive}:{origin_dir}',
              f'{dest_drive}:{dest_dir}{origin_dir}', '-P']
        rc_process = await exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        gid = ''.join(SystemRandom().choices(ascii_letters + digits, k=10))
        status_type= MirrorStatus.STATUS_COPYING
        rc_status= RcloneStatus(rc_process, self.__message, status_type, gid)
        status= await rc_status.start()
        if status:
            #Get Link
            cmd = ["rclone", "link", f'--config={conf_path}', f"{dest_drive}:{dest_dir}{origin_dir}"]
            process = await exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            out, err = await process.communicate()
            url = out.decode().strip()
            button.url_buildbutton("Cloud Link 🔗", url)
            return_code = await process.wait()
            if return_code != 0:
                LOGGER.info(err.decode().strip())
            #Calculate Size
            cmd = ["rclone", "size", f'--config={conf_path}', "--json", f"{dest_drive}:{dest_dir}{origin_dir}"]
            process = await exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            out, _ = await process.communicate()
            output = out.decode().strip()
            return_code = await process.wait()
            if return_code != 0:
                LOGGER.info(err.decode().strip())
            data = loads(output)
            files = data["count"]
            size = human_readable_bytes(data["bytes"])
            format_out = f"**Total Files** {files}\n" 
            format_out += f"**Total Size**: {size}"
            await editMessage(format_out, self.__message, reply_markup= button.build_menu(1))
        else:
            await editMessage("Copy Cancelled", self.__message)    
