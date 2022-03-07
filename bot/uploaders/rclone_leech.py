from configparser import ConfigParser
import os
import time
from pyrogram.errors import FloodWait
from pyrogram.errors.exceptions.bad_request_400 import MessageNotModified
from bot import SessionVars
from bot.uploaders.telegram_upload import upload_media_pyro
from ..core.get_vars import get_val
from bot.utils.get_rclone_conf import get_config
import logging
import subprocess
import asyncio
import re
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .progress_for_rclone import status

log = logging.getLogger(__name__)


async def rclone_downloader(client, user_msg, sender, origin_dir, dest_dir, folder= False, path= ""):

        await user_msg.edit("Preparing for download...")

        origin_drive = get_val("DEF_RCLONE_DRIVE")
        conf_path = await get_config()
        conf = ConfigParser()
        conf.read(conf_path)
        drive_name = ""

        for i in conf.sections():
            if origin_drive == str(i):
                if conf[i]["type"] == "drive":
                    log.info("Google Drive Download Detected.")
                else:
                    drive_name = conf[i]["type"]
                    log.info(f"{drive_name} Download Detected.")
                break

        log.info("Downloading...")
        log.info(f"{origin_drive}:{origin_dir}:{dest_dir}")

        rclone_copy_cmd = [
            'rclone', 'copy', f'--config={conf_path}', f'{origin_drive}:{origin_dir}', f'{dest_dir}', '-P']

        rclone_pr = subprocess.Popen(
            rclone_copy_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        rcres= await rclone_process_update(rclone_pr, user_msg)

        if rcres:
            rclone_pr.kill()
            await user_msg.edit("Download cancelled")
            return 

        await user_msg.delete()     

        if folder:
            for root, dirnames, filenames in os.walk(dest_dir):
                log.info("Files: {}".format(filenames))
                log.info("Directories: {}".format(dirnames))
                for i, file in enumerate(filenames):
                    timer = 60
                    if i < 25:
                        timer = 5
                    if i < 50 and i > 25:
                        timer = 10
                    if i < 100 and i > 50:
                        timer = 15
                    message= await client.send_message(sender, "Processing!")
                    file = os.path.join(root, file)
                    try:
                        await upload_media_pyro(client, message, sender, file)
                    except FloodWait as fw:
                        await asyncio.sleep(fw.seconds + 5)
                        await upload_media_pyro(client, message, sender, file)
                    protection = await client.send_message(sender, f"Sleeping for `{timer}` seconds...")
                    time.sleep(timer)
                    await protection.delete()  
            await client.send_message(sender, "Nothing else to upload!")  
        else:
            message= await client.send_message(sender, "Processing...")
            file = os.path.join(dest_dir, path)
            await upload_media_pyro(client, message, sender, file)

async def rclone_process_update(rclonepr, usermsg):
        blank=0    
        process = rclonepr
        user_message = usermsg
        sleeps = False
        msg = ""
        msg1 = ""
        
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

                    msg = "<b>Downloading...\n{} \n{} \nSpeed:- {} \nETA:- {}</b>".format(nstr[0],prg,nstr[2],nstr[3].replace("ETA",""))
                    
                    if msg1 != msg:
                        try:
                            await user_message.edit(text= msg, reply_markup=InlineKeyboardMarkup([[
                                InlineKeyboardButton("Cancel", callback_data= "upcancel")]]))    
                            msg1= msg
                        except MessageNotModified: 
                            pass                                
                        
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