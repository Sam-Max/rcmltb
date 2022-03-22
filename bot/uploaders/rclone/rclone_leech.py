from configparser import ConfigParser
from os import walk
import os
import time
from pyrogram.errors import FloodWait
from bot.core.get_vars import get_val
from bot.uploaders.rclone.progress_for_rclone import rclone_process_update_pyro
from bot.uploaders.telegram.telegram_upload import upload_media_pyro
from bot.utils.get_size_p import get_size
from bot.utils.misc_utils import clear_stuff
from bot.utils.zip_utils import split_in_zip
from bot.utils.get_rclone_conf import get_config
import logging
import subprocess
import asyncio

log = logging.getLogger(__name__)


async def rclone_downloader(client, user_msg, chat_id, origin_dir, dest_dir, folder= False, path= ""):

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

        rcres= await rclone_process_update_pyro(rclone_pr, user_msg)

        if rcres:
            rclone_pr.kill()
            await user_msg.edit("Download cancelled")
            return 

        tg_split_size= get_size(get_val("TG_SPLIT_SIZE")) 

        if folder:
            for dirpath, _, filenames in walk(dest_dir):
                if len(filenames) == 0:
                     continue 
                sorted_fn= sorted(filenames)
                for i, file in enumerate(sorted_fn):  
                    timer = 60  
                    if i < 25:
                        timer = 5
                    if i < 50 and i > 25:
                        timer = 10
                    if i < 100 and i > 50:
                        timer = 15
                    f_path = os.path.join(dirpath, file)
                    f_size = os.path.getsize(f_path)
                    if int(f_size) > get_val("TG_SPLIT_SIZE"):
                        message= await client.send_message(chat_id, f"File larger than {tg_split_size}, Splitting...")     
                        split_dir= await split_in_zip(f_path, size=get_val("TG_SPLIT_SIZE")) 
                        os.remove(f_path) 
                        dir_list= os.listdir(split_dir)
                        dir_list.sort() 
                        for file in dir_list :
                            f_path = os.path.join(split_dir, file)
                            try:
                                await upload_media_pyro(client, message, chat_id, f_path)
                            except FloodWait as fw:
                                await asyncio.sleep(fw.seconds + 5)
                                await upload_media_pyro(client, message, chat_id, f_path)     
                            time.sleep(timer)
                    else:
                        try:
                            await upload_media_pyro(client, user_msg, chat_id, f_path)
                        except FloodWait as fw:
                            await asyncio.sleep(fw.seconds + 5)
                            await upload_media_pyro(client, user_msg, chat_id, f_path)
                        time.sleep(timer)
            await clear_stuff("./Downloads")
            await client.send_message(chat_id, "Nothing else to upload!")  
        else:
            f_path = os.path.join(dest_dir, path)
            f_size = os.path.getsize(f_path)
            if int(f_size) > get_val("TG_SPLIT_SIZE"):
                message= await client.send_message(chat_id, f"File larger than {tg_split_size}, Splitting...")     
                split_dir= await split_in_zip(f_path, size=get_val("TG_SPLIT_SIZE")) 
                os.remove(f_path) 
                dir_list= os.listdir(split_dir)
                dir_list.sort() 
                for file in dir_list :
                    timer = 5
                    f_path = os.path.join(split_dir, file)
                    try:
                        await upload_media_pyro(client, message, chat_id, f_path)
                    except FloodWait as fw:
                        await asyncio.sleep(fw.seconds + 5)
                        await upload_media_pyro(client, message, chat_id, f_path)
                    time.sleep(timer)
                await clear_stuff("./Downloads")    
                await client.send_message(chat_id, "Nothing else to upload!")
            else:
                try:    
                    await upload_media_pyro(client, user_msg, chat_id, f_path)
                except FloodWait as fw:
                    await asyncio.sleep(fw.seconds + 5)
                    await upload_media_pyro(client, user_msg, chat_id, f_path)   

