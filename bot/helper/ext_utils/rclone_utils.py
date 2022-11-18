from json import loads as jsonloads
from re import escape
from os import path as ospath
from asyncio.subprocess import PIPE, create_subprocess_exec
from bot import LOGGER, OWNER_ID, config_dict
from bot.helper.ext_utils.filters import CustomFilters
from bot.helper.ext_utils.message_utils import sendMessage
from bot.helper.ext_utils.rclone_data_holder import get_rclone_data, update_rclone_data

            
async def is_remote_selected(user_id, message):
    if config_dict['MULTI_RCLONE_CONFIG'] or CustomFilters._owner_query(user_id):
        if DEFAULT_OWNER_REMOTE := config_dict['DEFAULT_OWNER_REMOTE']:
                if user_id == OWNER_ID:
                    update_rclone_data("MIRRORSET_REMOTE", DEFAULT_OWNER_REMOTE, user_id)
                    return True
        if get_rclone_data("MIRRORSET_REMOTE", user_id):
            return True
        else:
            await sendMessage("Select a cloud first, use /mirrorset", message)
            return False
    else:
        return True

async def is_rclone_config(user_id, message, isLeech=False):
    if config_dict['MULTI_RCLONE_CONFIG'] or CustomFilters._owner_query(user_id):
        path= ospath.join("users", f'{user_id}', "rclone.conf")
        if not ospath.exists(path):
            if isLeech:
                return False
            else:
                await sendMessage("Send a rclone config file, use /config", message)
                return False
        else:
            return True  
    else:
        path= ospath.join("users", "global_rclone", "rclone.conf")
        if not ospath.exists(path):
            await sendMessage("No global rclone file found", message)
            return False
        else:
            return True

def get_rclone_config(user_id):
    if config_dict['MULTI_RCLONE_CONFIG'] or CustomFilters._owner_query(user_id):
        rc_path = ospath.join("users", f"{user_id}" , "rclone.conf")
        if ospath.exists(rc_path):
            return rc_path
    else:
        rc_path = ospath.join("users", "global_rclone", "rclone.conf")      
        if ospath.exists(rc_path):
            return rc_path

async def get_gid(remote, path, ename, conf_path, isdir=True):
    name = escape(ename)
    if isdir:
        cmd = ["rclone", "lsjson", f'--config={conf_path}', f"{remote}:{path}", "--dirs-only",
                        "-f", f"+ {name}", "-f", "- *"]
    else:
        cmd = ["rclone", "lsjson", f'--config={conf_path}', f"{remote}:{path}", "--files-only",
                        "-f", f"+ {name}", "-f", "- *"]
    process = await create_subprocess_exec(*cmd,stdout= PIPE,stderr= PIPE)
    stdout, stderr = await process.communicate()
    return_code = await process.wait()
    stdout = stdout.decode().strip()
    if return_code != 0:
        err = stderr.decode().strip()
        LOGGER.error(f'Error: {err}') 
    try:
        data = jsonloads(stdout)
        id = data[0]["ID"]
        name = data[0]["Name"]
        return (id, name)
    except Exception:
        LOGGER.error("Error while getting id ::- {}".format(stdout))

        