from bot.utils.get_rclone_conf import get_config
import os, configparser, logging
from pyrogram.types import InlineKeyboardMarkup
from pyrogram.types import InlineKeyboardButton
from pyrogram.types import InlineKeyboardButton
import asyncio
import json
import logging
from bot.core.set_vars import set_val
from bot.utils.get_size_p import get_size
from bot.utils.pairwise_row import pairwise

torlog = logging.getLogger(__name__)

header = ""
folder_icon= "📁"

async def settings_leech_menu(
    client,
    message, 
    drive_base="", 
    edit=False, 
    msg="", 
    drive_name="", 
    data_cb="", 
    submenu=None, 
    data_back_cb=""
    ):
    
    menu = []
    btns= []

    if submenu is None:
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

    elif submenu == "list_drive":
        conf_path = await get_config()

        await list_selected_drive_leech(
            drive_base, 
            drive_name, 
            conf_path, 
            menu, 
            data_cb,
            data_back_cb
            )    

        menu.append(
            [InlineKeyboardButton("⬅️ Back", f"leechmenu^{data_back_cb}")]
        )

        menu.append(
            [InlineKeyboardButton("✘ Close Menu", f"leechmenu^selfdest")]
        )

        if edit:
            await message.edit(msg, reply_markup= InlineKeyboardMarkup(menu))
        else:
            await message.reply(header, reply_markup= InlineKeyboardMarkup(menu))

async def list_selected_drive_leech(
    drive_base, 
    drive_name, 
    conf_path, 
    menu, 
    data_cb,
    data_back_cb="",
    offset= 0, 
    ):

    menu.append([InlineKeyboardButton(f" ✅ Select this folder", callback_data= f"leechmenu^start_leech_folder")])
    
    cmd = ["rclone", "lsjson", f'--config={conf_path}', f"{drive_name}:{drive_base}" ] 

    process = await asyncio.create_subprocess_exec(
    *cmd,
    stdout=asyncio.subprocess.PIPE
    )

    stdout, _ = await process.communicate()
    stdout = stdout.decode().strip()

    try:
        data = json.loads(stdout)
    except Exception as e:
        logging.info(e)
        return

    if data == []:
         menu.append(
            [InlineKeyboardButton("❌Nothing to show❌", callback_data="leechmenu^pages")])
         return     

    data.sort(key=lambda x: x["Size"])  

    set_val("JSON_RESULT_DATA", data)
    data, next_offset, total= await get_list_drive_results_leech(data)
    
    list_drive_leech(data, menu, data_cb)

    if offset == 0 and total <= 10:
        menu.append(
            [InlineKeyboardButton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", callback_data="leechmenu^pages")]) 
            
    else: 
        menu.append(
            [InlineKeyboardButton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", callback_data="leechmenu^pages"),
             InlineKeyboardButton("NEXT ⏩", callback_data= f"n_leech {next_offset} {data_back_cb}")
            ])
           
async def get_list_drive_results_leech(data, max_results=10, offset=0):
    total = len(data)
    next_offset = offset + max_results
    data = await list_range(offset, max_results, data)
    return data, next_offset, total    

async def list_range(offset, max_results, data):
    start = offset
    end = max_results + start
    
    if end > len(data):
        return data[offset:]    

    if offset >= len(data):
        return []    
    
    return data[start:end]             

def list_drive_leech(
    result, 
    menu=[], 
    data_cb=""
    ):
     folder = ""
     index= 0
     for i in result:
        path = i["Path"]
        path == path.strip()
        index= index + 1
        set_val(f"{index}", path)
        size= i['Size']
        size= get_size(size)
        mime_type= i['MimeType']
        if mime_type == 'inode/directory': 
            folder= "📁"
            menu.append(  
            [InlineKeyboardButton(f"{folder} {path}", f"leechmenu^{data_cb}^{index}")]
        )
        else:
            menu.append(        
            [InlineKeyboardButton(f"[{size}] {path}", f"leechmenu^start_leech^{index}")]
        )