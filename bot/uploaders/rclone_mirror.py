from configparser import ConfigParser
from html import escape
import time
from bot import SessionVars
from bot.utils.drive_utils import get_glink
from bot.utils.rename_file import rename
from ..core.get_vars import get_val
from bot.utils.get_rclone_conf import get_config
import os
import logging
import subprocess
import asyncio
import re
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .progress_for_rclone import status

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

    rcres= await rclone_process_update(rclone_pr, user_msg)

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

async def rclone_process_update(rclone_pr, user_msg):
        blank=0    
        process = rclone_pr
        user_message = user_msg
        sleeps = False
        start = time.time()
        edit_time= 10
        
        while True:
            data = process.stdout.readline().decode()
            data = data.strip()
            mat = re.findall("Transferred:.*ETA.*",data)
           
            if mat is not None:
                if len(mat) > 0:
                    sleeps = True
                    nstr = mat[0].replace("Transferred:","")
                    nstr = nstr.strip()
                    nstr = nstr.split(",")
                    percent = nstr[1].strip("% ")
                    try:
                        percent = int(percent)
                    except:
                        percent = 0
                    prg = status(percent)

                    msg = "<b>Uploading...\n{} \n{} \nSpeed:- {} \nETA:- {}</b>".format(nstr[0],prg,nstr[2],nstr[3].replace("ETA",""))
                    
                    if time.time() - start > edit_time:
                         start = time.time()
                         await user_message.edit(text= msg, reply_markup=InlineKeyboardMarkup([[
                                InlineKeyboardButton("Cancel", callback_data= "upcancel")]]))    
                        
            if data == "":
                blank += 1
                if blank == 20:
                    break
            else:
                blank = 0

            if sleeps:               
                sleeps= False
                if get_val("UPLOAD_CANCEL"):
                    SessionVars.update_var("UPLOAD_CANCEL", False)
                    return True
                await asyncio.sleep(2)
                process.stdout.flush()    

   
