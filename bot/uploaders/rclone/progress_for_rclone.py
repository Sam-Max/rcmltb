import time
import asyncio
import re
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from telethon import Button
from ... import SessionVars
from bot.core.get_vars import get_val

async def rclone_process_update_pyro(rclone_pr, user_msg, status_message):
        blank=0    
        process = rclone_pr
        user_message = user_msg
        sleeps = False
        start = time.time()
        edit_time= get_val("EDIT_SLEEP_SECS")
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
                    prg = progress(percent)

                    msg = "<b>{}...\n{} \n{} \nSpeed:- {} \nETA:- {}</b>".format(status_message, nstr[0],prg,nstr[2],nstr[3].replace("ETA",""))
                    
                    if time.time() - start > edit_time:
                         if msg1 != msg:
                            start = time.time()
                            await user_message.edit(text= msg, reply_markup=InlineKeyboardMarkup([[
                                    InlineKeyboardButton("Cancel", callback_data= "upcancel")]]))  
                            msg1= msg  
                        
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

async def rclone_process_update_tele(rclone_pr, message):
    blank = 0
    process = rclone_pr
    user_message = message
    sleeps = False
    start = time.time()
    edit_time= get_val("EDIT_SLEEP_SECS")
    msg = ""
    msg1 = ""

    while True:
        data = process.stdout.readline().decode().strip()
        mat = re.findall("Transferred:.*ETA.*", data)

        if mat is not None:
            if len(mat) > 0:
                sleeps = True
                nstr = mat[0].replace("Transferred:", "")
                nstr = nstr.strip()
                nstr = nstr.split(",")
                percent = nstr[1].strip("% ")
                try:
                    percent = int(percent)
                except:
                    percent = 0
                prg = progress(percent)

                msg = '**Copying...\n{} \n{} \nSpeed:- {} \nETA:- {}\n**'.format(nstr[0], prg, nstr[2], nstr[3].replace("ETA", ""))
                
                if time.time() - start > edit_time:
                    if msg1 != msg:
                        start = time.time()
                        await user_message.edit(text=msg, buttons= [[Button.inline("Cancel", "upcancel")]])
                        msg1= msg

        if data == "":
            blank += 1
            if blank == 20:
                break
        else:
            blank = 0

        if sleeps:
            sleeps = False
            if get_val("UPLOAD_CANCEL"):
                SessionVars.update_var("UPLOAD_CANCEL", False)
                return True
            await asyncio.sleep(2)
            process.stdout.flush()   

def progress(val):
    if val < 10:
        progress = "[▫️▫️▫️▫️▫️▫️▫️▫️▫️▫️]"

    if val >= 10 and val <= 19:
        progress = "[▪️▫️▫️▫️▫️▫️▫️▫️▫️▫️]"

    if val >= 20 and val <= 29:
        progress = "[▪️▪️▫️▫️▫️▫️▫️▫️▫️▫️]"

    if val >= 30 and val <= 39:
        progress = "[▪️▪️▪️▫️▫️▫️▫️▫️▫️▫️]"

    if val >= 40 and val <= 49:
        progress = "[▪️▪️▪️▪️▫️▫️▫️▫️▫️▫️]"

    if val >= 50 and val <= 59:
        progress = "[▪️▪️▪️▪️▪️▫️▫️▫️▫️▫️]"

    if val >= 60 and val <= 69:
        progress = "[▪️▪️▪️▪️▪️▪️▫️▫️▫️▫️]"

    if val >= 70 and val <= 79:
        progress = "[▪️▪️▪️▪️▪️▪️▪️▫️▫️▫️]"

    if val >= 80 and val <= 89:
        progress = "[▪️▪️▪️▪️▪️▪️▪️▪️▫️▫️]"

    if val >= 90 and val <= 99:
        progress = "[▪️▪️▪️▪️▪️▪️▪️▪️▪️▫️]"

    if val == 100:
        progress = "[▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️]"

    return progress
