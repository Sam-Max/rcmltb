from os import path as ospath, getcwd
from configparser import ConfigParser
from pyrogram.types import InlineKeyboardMarkup
import asyncio
from json import loads as jsonloads
from bot.core.varholderwrap import set_val
from bot.utils.bot_utils.menu_utils import Menus, rcloneListButtonMaker
from bot.utils.bot_utils.message_utils import editMessage, sendMarkup, sendMessage
from bot.utils.bot_utils.misc_utils import ButtonMaker, get_rclone_config, pairwise

folder_icon= "📁"

async def myfiles_menu(
    client,
    message, 
    msg ="", 
    edit=False, 
    drive_name="", 
    drive_base="", 
    data_cb="", 
    submenu="", 
    data_back_cb=""
    ):
    
    buttons = ButtonMaker()

    if submenu == "list_drive":
        path= ospath.join(getcwd(), "rclone.conf")
        conf = ConfigParser()
        conf.read(path)

        for j in conf.sections():
            if "team_drive" in list(conf[j]):
                buttons.cb_buildsecbutton(f"{folder_icon} {j}", f"myfilesmenu^{data_cb}^{j}")
            else:
                buttons.cb_buildsecbutton(f"{folder_icon} {j}", f"myfilesmenu^{data_cb}^{j}")

        for a, b in pairwise(buttons.second_button):
            row= [] 
            if b == None:
                row.append(a)  
                buttons.ap_buildbutton(row)
                break
            row.append(a)
            row.append(b)
            buttons.ap_buildbutton(row)

        buttons.cbl_buildbutton("✘ Close Menu", f"myfilesmenu^close")

        if edit:
            await editMessage(msg, message, reply_markup= InlineKeyboardMarkup(buttons.first_button))
        else:
            await sendMarkup(msg, message, reply_markup= InlineKeyboardMarkup(buttons.first_button))

    elif submenu == "list_dir":
        path = get_rclone_config()
        buttons.cbl_buildbutton(f"⚙️ Folder Settings", f"myfilesmenu^start_folder_actions")
    
        cmd = ["rclone", "lsjson", f'--config={path}', f"{drive_name}:{drive_base}" ] 
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
            buttons.cbl_buildbutton("❌Nothing to show❌", data="myfilesmenu^pages")   
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
                    menu_type= Menus.MYFILES, 
                    callback = data_cb)

            if offset == 0 and total <= 10:
               buttons.cbl_buildbutton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", data="myfilesmenu^pages") 
            else: 
               buttons.dbuildbutton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", "myfilesmenu^pages",
                                     "NEXT ⏩", f"n_myfiles {next_offset} {data_back_cb}")   

        buttons.cbl_buildbutton("⬅️ Back", f"myfilesmenu^{data_back_cb}")
        buttons.cbl_buildbutton("✘ Close Menu", "myfilesmenu^close")

        if edit:
            await editMessage(msg, message, reply_markup= InlineKeyboardMarkup(buttons.first_button))
        else:
            await sendMarkup(msg, message, reply_markup= InlineKeyboardMarkup(buttons.first_button))