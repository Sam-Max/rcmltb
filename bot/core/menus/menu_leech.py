from json import loads as jsonloads
from os import path as ospath, getcwd
from configparser import ConfigParser
import asyncio
from pyrogram.types import InlineKeyboardMarkup
from bot.core.varholderwrap import set_val
from bot.utils.bot_utils.menu_utils import Menus, rcloneListButtonMaker
from bot.utils.bot_utils.message_utils import editMessage, sendMarkup, sendMessage
from bot.utils.bot_utils.misc_utils import ButtonMaker, get_rclone_config, pairwise

folder_icon= "📁"

async def leech_menu(
    client,
    message, 
    msg="",
    edit=False, 
    drive_base="", 
    drive_name="", 
    submenu="", 
    data_cb="", 
    data_back_cb=""
    ):

    buttons = ButtonMaker()

    if submenu == "list_drive":
        path= ospath.join(getcwd(), "rclone.conf")
        conf = ConfigParser()
        conf.read(path)

        for j in conf.sections():
            if "team_drive" in list(conf[j]):
                buttons.cb_buildsecbutton(f"{folder_icon} {j}", f"leechmenu^{data_cb}^{j}")     
            else:
                buttons.cb_buildsecbutton(f"{folder_icon} {j}", f"leechmenu^{data_cb}^{j}")          
        
        for a, b in pairwise(buttons.second_button):
            row= []
            if b == None:
                row.append(a)     
                buttons.ap_buildbutton(row)
                break
            row.append(a)
            row.append(b)
            buttons.ap_buildbutton(row)
            
        buttons.cbl_buildbutton("✘ Close Menu", f"leechmenu^close")

        if edit:
            await editMessage(msg, message, reply_markup= InlineKeyboardMarkup(buttons.first_button))
        else:
            await sendMarkup(msg, message, reply_markup= InlineKeyboardMarkup(buttons.first_button))

    elif submenu == "list_dir":
        path = get_rclone_config()
        buttons.cbl_buildbutton("✅ Select this folder", data="leechmenu^start_leech_folder")
        
        cmd = ["rclone", "lsjson", f'--config={path}', f"{drive_name}:{drive_base}"]
        process = await asyncio.create_subprocess_exec(*cmd, 
                    stdout=asyncio.subprocess.PIPE, 
                    stderr=asyncio.subprocess.PIPE)
        out, err = await process.communicate()
        out = out.decode().strip()
        return_code = await process.wait()

        if return_code != 0:
           err = err.decode().strip()
           return await sendMessage(f'Error: {err}', message)

        list_info = jsonloads(out)
        list_info.sort(key=lambda x: x["Size"])
        set_val("list_info", list_info)

        if len(list_info) == 0:
            buttons.cbl_buildbutton("❌Nothing to show❌", data="leechmenu^pages")   
        else:
            total = len(list_info)
            max_results= 10
            offset= 0
            start = offset
            end = max_results + start
            next_offset = offset + max_results

            if end > total:
                list_info= list_info[offset:]    
            elif offset >= total:
                list_info= []    
            else:
                list_info= list_info[start:end]  

            rcloneListButtonMaker(result_list= list_info,
                buttons=buttons,
                menu_type= Menus.LEECH, 
                callback = data_cb
            )

            if offset == 0 and total <= 10:
                buttons.cbl_buildbutton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", data="leechmenu^pages")        
            else: 
                buttons.dbuildbutton(first_text= f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", first_callback="leechmenu^pages",
                                second_text= "NEXT ⏩", second_callback= f"n_leech {next_offset} {data_back_cb}")
    
        buttons.cbl_buildbutton("⬅️ Back", data= f"leechmenu^{data_back_cb}")
        buttons.cbl_buildbutton("✘ Close Menu", data="leechmenu^close")

        if edit:
            await editMessage(msg, message, reply_markup= InlineKeyboardMarkup(buttons.first_button))
        else:
            await sendMarkup(msg, message, reply_markup= InlineKeyboardMarkup(buttons.first_button))


 
    
           