# -*- coding: utf-8 -*-

from configparser import ConfigParser
from pyrogram.errors.exceptions.bad_request_400 import MessageNotModified
from bot import SessionVars
from ..core.getVars import get_val
import os
import logging
import subprocess
import asyncio
import re
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.raw.types import KeyboardButtonUrl
from .progress_for_rclone import status

log = logging.getLogger(__name__)


class RcloneUploader():

    def __init__(self, path, user_msg, dest_drive=None):
        super().__init__()
        self._path = path
        self._user_msg = user_msg
        self._rclone_pr = None
        self._dest_drive = dest_drive
        self.dest_base= None

    async def execute(self):
        path = self._path
       
        if self._dest_drive is None:
            dest_drive = get_val("DEF_RCLONE_DRIVE")
        else:
            dest_drive = self._dest_drive

        conf_path = await self.get_config()

        if conf_path is None:
            await self._user_msg.reply("No se encontró el archivo de configuración rclone.")
            return 

        conf = ConfigParser()
        conf.read(conf_path)
        general_drive_name = ""

        for i in conf.sections():
            if dest_drive == str(i):
                if conf[i]["type"] == "drive":
                    self.dest_base = get_val("BASE_DIR")
                    log.info("Google Drive Upload Detected.")
                else:
                    general_drive_name = conf[i]["type"]
                    self.dest_base = get_val("BASE_DIR")
                    log.info(f"{general_drive_name} Upload Detected.")
                break

        if not os.path.exists(path):
            await self._user_msg.reply("the path {path} not found")
            return 

        if os.path.isdir(path):
            new_dest_base = os.path.join(self.dest_base, os.path.basename(path))
            rclone_copy_cmd = ['rclone', 'copy', f'--config={conf_path}', str(path),
                                    f'{dest_drive}:{new_dest_base}', '-P']

            rclone_pr = subprocess.Popen(
                rclone_copy_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            log.info(f'{dest_drive}:{new_dest_base}')
            log.info("Uploading...")

            self._rclone_pr = rclone_pr
            rcres= await self.rclone_process_update()

            # if(await self.check_errors(rclone_pr, self._user_msg)):
            #     return
        
            if rcres:
                rclone_pr.kill()
                log.info("subida cancelada")
                await self._user_msg.edit("Subida cancelada")
                return 
            
            log.info("subida exitosa")
            await self._user_msg.edit("Subida exitosa ✅")

        else:
            new_dest_base = self.dest_base
            rclone_copy_cmd = ['rclone', 'copy', f'--config={conf_path}', str(path),
                                    f'{dest_drive}:{new_dest_base}', '-P']
            
            log.info(f'{dest_drive}:{new_dest_base}')
            log.info("Uploading...")

            rclone_pr = subprocess.Popen(
                rclone_copy_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self._rclone_pr = rclone_pr
            rcres= await self.rclone_process_update()


            # if(await self.check_errors(rclone_pr, self._user_msg)):
            #     return
        
            if rcres:
                rclone_pr.kill()
                log.info("subida cancelada")
                await self._user_msg.edit("Subida cancelada")
                return 
            
            log.info("subida exitosa")
            await self._user_msg.edit("Subida exitosa ✅")


    async def rclone_process_update(self):
        blank=0    
        process = self._rclone_pr
        user_message = self._user_msg
        sleeps = False
        #start = time.time()
        msg = ""
        msg1 = ""
        #edit_time = get_val("EDIT_SLEEP_SECS")
        
        while True:
            data = process.stdout.readline().decode()
            data = data.strip()
            mat = re.findall("Transferred:.*ETA.*",data)
           
            if mat is not None:
                if len(mat) > 0:
                    sleeps = True
                    #if time.time() - start > edit_time:
                        #start = time.time()
                    nstr = mat[0].replace("Transferred:","")
                    nstr = nstr.strip()
                    nstr = nstr.split(",")
                    percent = nstr[1].strip("% ")
                    try:
                        percent = int(percent)
                    except:
                        percent = 0
                    prg = status(percent)

                    msg = "<b>Subiendo...\n{} \n{} \nVelocidad:- {} \nETA:- {}</b>".format(nstr[0],prg,nstr[2],nstr[3].replace("ETA",""))
                    
                    if msg1 != msg:
                        try:
                            await user_message.edit(text= msg, reply_markup=InlineKeyboardMarkup([[
                                InlineKeyboardButton("Cancel", callback_data= "upcancel")]]))    
                            msg1= msg
                        except Exception: 
                            log.info("Exception ocurred at line 148 on rclone_upload")  
                            pass                                
                        
            if data == "":
                blank += 1
                if blank == 20:
                    break
            else:
                blank = 0

            if sleeps:               
                sleeps= False
                if get_val("UP_CANCEL"):
                    SessionVars.update_var("UP_CANCEL", False)
                    return True
                await asyncio.sleep(2)
                process.stdout.flush()    

    async def get_config(self):
        config = os.path.join(os.getcwd(), 'rclone.conf')
        if config is not None:
            if isinstance(config, str):
                if os.path.exists(config):
                    return config

        return None

    # async def check_errors(self, rclone, usermsg):
    #     blank = 0
    #     while True:
    #         data = rclone.stderr.readline().decode()
    #         data = data.strip()
    #         if data == "":
    #             blank += 1
    #             if blank == 5:
    #                 break
    #         else:
    #             mat= data
    #             if mat is not None:
    #                 if len(mat) > 0:
    #                     log.info(f'Error:-{mat}')
    #                     await usermsg.edit(mat)
    #                     return True            

   
