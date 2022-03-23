from configparser import ConfigParser
from html import escape
from bot.core.get_vars import get_val
from bot.uploaders.rclone.progress_for_rclone import rclone_process_update_pyro
from bot.utils.drive_utils import get_glink
from bot.utils.rename_file import rename
from bot.utils.get_rclone_conf import get_config
import os
import logging
import subprocess
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

log = logging.getLogger(__name__)

async def rclone_uploader(path, user_msg, new_name, tag, is_rename= False):

    rclone_pr = None
    dest_base= None
    old_path = path
    dest_drive = get_val("DEF_RCLONE_DRIVE")

    conf_path = await get_config()
    conf = ConfigParser()
    conf.read(conf_path)
    gen_drive_name = ""

    for i in conf.sections():
        if dest_drive == str(i):
            if conf[i]["type"] == "drive":
                is_gdrive = True
                dest_base = get_val("BASE_DIR")
                log.info("Google Drive Upload Detected.")
            else:
                is_gdrive = False
                gen_drive_name = conf[i]["type"]
                dest_base = get_val("BASE_DIR")
                log.info(f"{gen_drive_name} Upload Detected.")
            break

    if not os.path.exists(old_path):
        await user_msg.reply("the path {path} not found")
        return 

    if is_rename:
        path = await rename(old_path, new_name)
    else:
        path= old_path    
            
    rclone_copy_cmd = ['rclone', 'copy', f'--config={conf_path}', str(path),
                            f'{dest_drive}:{dest_base}', '-P']

    log.info("Uploading...")

    rclone_pr = subprocess.Popen(
        rclone_copy_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    status_message= "Uploading"
    rcres= await rclone_process_update_pyro(rclone_pr, user_msg, status_message)

    if rcres:
        rclone_pr.kill()
        await user_msg.edit("Upload cancelled")
        return 
    
    log.info("Successfully uploaded")
    
    name= path.split("/")[-1]
    msg= "Successfully uploaded ✅\n\n"
    msg += f'<b>Name: </b><code>{escape(name)}</code><b>'

    if is_gdrive:
        gid = await get_glink(dest_drive, dest_base, os.path.basename(path), conf_path, False)
        link = f"https://drive.google.com/file/d/{gid[0]}/view"

        button= []
        button.append([InlineKeyboardButton(text = "Drive Link", url = link)])

        await user_msg.edit(f"{msg}\n\n<b>cc: </b>{tag}", reply_markup= InlineKeyboardMarkup(button))
    else:
        await user_msg.edit(f"{msg}\n\n<b>cc: </b>{tag}")

 

   
