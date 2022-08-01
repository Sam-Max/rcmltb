import os
from configparser import ConfigParser
import asyncio
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
from bot.core.set_vars import set_val
from bot.utils.bot_utils.menu_utils import menu_maker_for_rclone
from bot.utils.bot_utils.misc_utils import get_rclone_config, pairwise

header = ""
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

    menu = []
    btns= []

    if submenu == "list_drive":
        path= os.path.join(os.getcwd(), "rclone.conf")
        conf = ConfigParser()
        conf.read(path)

        for j in conf.sections():
            if "team_drive" in list(conf[j]):
                btns.append(InlineKeyboardButton(f"{folder_icon} {j}", f"leechmenu^{data_cb}^{j}"))
            else:
                btns.append(InlineKeyboardButton(f"{folder_icon} {j}", f"leechmenu^{data_cb}^{j}"))
        
        for a, b in pairwise(btns):
            row= [] 
            if b == None:
                row.append(a)  
                menu.append(row)
                break
            row.append(a)
            row.append(b)
            menu.append(row)

        menu.append(
            [InlineKeyboardButton("✘ Close Menu", f"leechmenu^selfdest")]
        )
        if edit:
           await message.edit(msg, reply_markup= InlineKeyboardMarkup(menu))
        else:
           await message.reply_text(msg, quote= True, reply_markup= InlineKeyboardMarkup(menu))

    elif submenu == "list_dir":
        path = get_rclone_config()
        
        menu.append([InlineKeyboardButton(f" ✅ Select this folder", callback_data= f"leechmenu^start_leech_folder")])
        
        cmd = ["rclone", "lsjson", f'--config={path}', f"{drive_name}:{drive_base}"]
        process = await asyncio.create_subprocess_exec(*cmd, 
                    stdout=asyncio.subprocess.PIPE, 
                    stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()
        stdout = stdout.decode().strip()
        return_code = await process.wait()

        if return_code != 0:
           stderr = stderr.decode().strip()
           return await message.reply_text(f'Error: {stderr}', quote=True)

        list_info = json.loads(stdout)
        list_info.sort(key=lambda x: x["Size"])
        set_val("JSON_RESULT_DATA", list_info)

        if len(list_info) == 0:
            menu.append([InlineKeyboardButton("❌Nothing to show❌", callback_data="leechmenu^pages")])
            menu.append([InlineKeyboardButton("⬅️ Back", callback_data=f"leechmenu^{data_back_cb}")])
            menu.append([InlineKeyboardButton("✘ Close Menu", callback_data=f"leechmenu^selfdest")])
           
            if edit:
                return await message.edit(msg, reply_markup= InlineKeyboardMarkup(menu))
            else:
                return await message.reply(header, reply_markup= InlineKeyboardMarkup(menu))
        
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

        menu_maker_for_rclone(list_info, menu, data_cb)    

        if offset == 0 and total <= 10:
            menu.append([InlineKeyboardButton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", callback_data="leechmenu^pages")]) 
        else: 
            menu.append([InlineKeyboardButton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", callback_data="leechmenu^pages"),
                InlineKeyboardButton("NEXT ⏩", callback_data= f"n_leech {next_offset} {data_back_cb}")])
        
        menu.append([InlineKeyboardButton("⬅️ Back", f"leechmenu^{data_back_cb}")])
       
        menu.append([InlineKeyboardButton("✘ Close Menu", f"leechmenu^selfdest")])

        if edit:
            await message.edit(msg, reply_markup= InlineKeyboardMarkup(menu))
        else:
            await message.reply(header, reply_markup= InlineKeyboardMarkup(menu))


 
    
           