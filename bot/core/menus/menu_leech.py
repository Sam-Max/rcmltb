import os, configparser
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import json
from bot import LOGGER
from bot.core.set_vars import set_val
from bot.utils.bot_utils.misc_utils import get_rclone_config, get_readable_size, pairwise

header = ""
folder_icon= "📁"

async def leech_menu(
    client,
    message, 
    msg="",
    edit=False, 
    isZip=False, 
    extract=False, 
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
        conf = configparser.ConfigParser()
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
        
        max_results= 10
        offset=0
        conf_path = get_rclone_config()
        
        menu.append([InlineKeyboardButton(f" ✅ Select this folder", callback_data= f"leechmenu^start_leech_folder")])
        cmd = ["rclone", "lsjson", f'--config={conf_path}', f"{drive_name}:{drive_base}" ] 
        process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE)
        stdout, _ = await process.communicate()
        stdout = stdout.decode().strip()

        try:
            dir_info = json.loads(stdout)
            dir_info.sort(key=lambda x: x["Size"])
            set_val("JSON_RESULT_DATA", dir_info)
        except Exception as e:
            return await message.reply_text(e, quote=True)

        if len(dir_info) == 0:
           return menu.append([InlineKeyboardButton("❌Nothing to show❌", callback_data="leechmenu^pages")])

        total = len(dir_info)
        next_offset = offset + max_results
        start = offset
        end = max_results + start
        
        if end > len(dir_info):
            dir_info[offset:]    
        elif offset >= len(dir_info):
            dir_info= []    
        else:
            dir_info[start:end]    

        list_dir_info(dir_info, menu, data_cb, isZip= isZip, extract= extract)    

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

def list_dir_info(dir_info, menu, data_callback, isZip, extract):
    folder = ""
    index= 0
    for dir in dir_info:
        path = dir["Path"]
        index += 1
        set_val(f"{index}", path)
        size= dir['Size']
        size= get_readable_size(size)
        mime_type= dir['MimeType']
        if mime_type == 'inode/directory': 
            folder= "📁"
            menu.append([InlineKeyboardButton(f"{folder} {path}", f"leechmenu^{data_callback}^{index}^{isZip}^{extract}")])
        else:
            menu.append([InlineKeyboardButton(f"[{size}] {path}", f"leechmenu^start_leech_file^{index}^{isZip}^{extract}")])
 
    
           