import asyncio
import json
from os import getcwd, path as ospath
import re
from bot import LOGGER
from bot.helper.ext_utils.message_utils import sendMessage
from bot.helper.ext_utils.var_holder import get_rclone_var

async def get_gid(drive_name, drive_base, ent_name, conf_path, isdir=True):
    name = re.escape(ent_name)
    if isdir:
        cmd = ["rclone", "lsjson", f'--config={conf_path}', f"{drive_name}:{drive_base}", "--dirs-only",
                        "-f", f"+ {name}", "-f", "- *"]
    else:
        cmd = ["rclone", "lsjson", f'--config={conf_path}', f"{drive_name}:{drive_base}", "--files-only",
                        "-f", f"+ {name}", "-f", "- *"]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout= asyncio.subprocess.PIPE,
        stderr= asyncio.subprocess.PIPE)

    stdout, stderr = await process.communicate()
    return_code = await process.wait()
    stdout = stdout.decode().strip()

    if return_code != 0:
        err = stderr.decode().strip()
        LOGGER.error(f'Error: {err}') 

    try:
        data = json.loads(stdout)
        id = data[0]["ID"]
        name = data[0]["Name"]
        return (id, name)
    except Exception:
        LOGGER.error("Error while getting id ::- {}".format(stdout))
            
async def is_not_drive(user_id, message):
    if len(get_rclone_var("MIRRORSET_DRIVE", str(user_id))) == 0:
        await sendMessage("Select a cloud first, use /mirrorset", message)
        return True

async def is_not_config(user_id, message):
    path= ospath.join(getcwd(), "users", str(user_id), "rclone.conf")
    if not ospath.exists(path):
        await sendMessage("Send an rclone config file, use /config", message)
        return True