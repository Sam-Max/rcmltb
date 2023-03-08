from configparser import ConfigParser
from json import loads as jsonloads
from re import escape as rescape
from os import path as ospath
from asyncio.subprocess import PIPE, create_subprocess_exec
from bot import LOGGER, OWNER_ID, config_dict, remotes_data
from bot.helper.ext_utils.filters import CustomFilters
from bot.helper.ext_utils.message_utils import editMessage, sendMarkup, sendMessage
from bot.helper.ext_utils.button_build import ButtonMaker
from bot.helper.ext_utils.rclone_data_holder import get_rclone_data, update_rclone_data

            
            
async def is_remote_selected(user_id, message):
    if config_dict['MULTI_RCLONE_CONFIG'] or CustomFilters._owner_query(user_id):
        if DEFAULT_OWNER_REMOTE := config_dict['DEFAULT_OWNER_REMOTE']:
                if user_id == OWNER_ID:
                    update_rclone_data("CLOUDSEL_REMOTE", DEFAULT_OWNER_REMOTE, user_id)
                    return True
        if get_rclone_data("CLOUDSEL_REMOTE", user_id) or len(remotes_data) > 0:
            return True
        else:
            await sendMessage("Select a cloud first, use /cloudselect", message)
            return False
    else:
        return True

async def is_rclone_config(user_id, message, isLeech=False):
    if config_dict['MULTI_RCLONE_CONFIG'] or CustomFilters._owner_query(user_id):
        path= ospath.join("users", f'{user_id}', "rclone.conf")
        if ospath.exists(path):
            return True
        else:
            if isLeech:
                return True
            else:
                await sendMessage("Send a rclone config file, use /botfiles command", message)
                return False
    else:
        path= ospath.join("users", "grclone", "rclone.conf")
        if ospath.exists(path):
            return True
        else:
            if isLeech:
                return True
            else:
                await sendMessage("Global rclone not found", message)
                return False

def get_rclone_config(user_id):
    if config_dict['MULTI_RCLONE_CONFIG'] or CustomFilters._owner_query(user_id):
        rc_path = ospath.join("users", f"{user_id}" , "rclone.conf")
        if ospath.exists(rc_path):
            return rc_path
    else:
        rc_path = ospath.join("users", "grclone", "rclone.conf")      
        if ospath.exists(rc_path):
            return rc_path

async def list_remotes(message, rclone_remote, base_dir, callback, edit=False):
    user_id= message.from_user.id
    buttons = ButtonMaker()
    path= get_rclone_config(user_id)
    conf = ConfigParser()
    conf.read(path)
    for remote in conf.sections():
        prev = ""
        if remote == get_rclone_data("CLOUDSEL_REMOTE", user_id):
            prev = "✅"
        buttons.cb_buildbutton(f"{prev} 📁 {remote}", f"{callback}^remote^{remote}^{message.id}")
    buttons.cb_buildbutton("✘ Close Menu", f"{callback}^close^{message.id}", 'footer')
    msg= f"Select cloud where you want to upload file\n\n<b>Path:</b><code>{rclone_remote}:{base_dir}</code>" 
    if edit:
        await editMessage(msg, message, reply_markup= buttons.build_menu(2))
    else:
        await sendMarkup(msg, message, reply_markup= buttons.build_menu(2))


async def get_gdlink(remote, base, name, conf, type, buttons):
    if type == "Folder":
        name = name.replace(".", "")
        ename = rescape(name)
        cmd = ["rclone", "lsjson", f'--config={conf}', f"{remote}:{base}", "--dirs-only", "-f", f"+ {ename}/", "-f", "- *"]
    else:
        ename = rescape(name)
        cmd = ["rclone", "lsjson", f'--config={conf}', f"{remote}:{base}", "--files-only", "-f", f"+ {ename}", "-f", "- *"]
    LOGGER.info(cmd)
    process = await create_subprocess_exec(*cmd,stdout= PIPE,stderr= PIPE)
    stdout, stderr = await process.communicate()
    return_code = await process.wait()
    stdout = stdout.decode().strip()
    if return_code != 0:
        err = stderr.decode().strip()
        LOGGER.error(f'Error: {err}') 
        return
    try:
        data = jsonloads(stdout)
        id = data[0]["ID"]
        if type == "Folder":
            link = f"https://drive.google.com/folderview?id={id}"
            buttons.url_buildbutton('Cloud Link 🔗', link)
        else:
            link = f"https://drive.google.com/file/d/{id}/view"
            buttons.url_buildbutton('Cloud Link 🔗', link)
    except Exception:
        buttons.cb_buildbutton("🚫", "close")
        LOGGER.error("Error while getting id")
    
    
        

        