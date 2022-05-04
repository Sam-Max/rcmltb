from telethon.tl.types import KeyboardButtonCallback
from bot.utils.get_rclone_conf import get_config
from bot.utils.pairwise_row import pairwise
from ..get_vars import get_val
import os, configparser, logging
from telethon.tl.types import KeyboardButtonCallback
import asyncio
import json
import logging
from bot.core.set_vars import set_val

torlog = logging.getLogger(__name__)

yes = "✅"
folder_icon= "📁"
header = ""

async def settings_main_menu(
    query, 
    mmes="", 
    drive_base="", 
    edit=False, 
    msg="", 
    drive_name="", 
    data_cb="", 
    submenu=None, 
    data_back_cb= ""
    ):
   
    menu = []
    btns= []

    if submenu is None:
        path= os.path.join(os.getcwd(), "rclone.conf")
        conf = configparser.ConfigParser()
        conf.read(path)

        def_drive = get_val("DEF_RCLONE_DRIVE")

        for j in conf.sections():
            prev = ""
            if j == def_drive:
                prev = yes

            if "team_drive" in list(conf[j]):
                btns.append(KeyboardButtonCallback(f"{prev} {folder_icon} {j}", f"mainmenu^list_drive_main_menu^{j}"))
            else:
                btns.append(KeyboardButtonCallback(f"{prev} {folder_icon} {j}", f"mainmenu^list_drive_main_menu^{j}"))
        
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
            [KeyboardButtonCallback("✘ Close Menu", f"mainmenu^selfdest")]
        )

        base_dir= get_val("BASE_DIR")
        rclone_drive = get_val("DEF_RCLONE_DRIVE")
        msg= f"Select cloud where you want to upload file\n\nPath:`{rclone_drive}:{base_dir}`"

        if edit:
            await mmes.edit(msg, buttons=menu)
        else:
            await query.reply(header + msg, buttons=menu)


    elif submenu == "list_drive":
        conf_path = await get_config()

        await list_selected_drive(
            query, 
            drive_base, 
            drive_name, 
            conf_path, 
            data_cb, 
            menu,
            data_back_cb 
            )

        menu.append(
            [KeyboardButtonCallback("⬅️ Back", f"mainmenu^{data_back_cb}")]
        )

        menu.append(
            [KeyboardButtonCallback("✘ Close Menu", f"mainmenu^selfdest")]
        )

        if edit:
            await mmes.edit(msg, buttons=menu)
        else:
            await query.reply(header, buttons=menu)

async def list_selected_drive(
    query, 
    drive_base, 
    drive_name, 
    conf_path, 
    data_cb, 
    menu, 
    data_back_cb="",
    offset= 0
    ):
    menu.append([KeyboardButtonCallback(f" ✅ Select this folder", f"mainmenu^selfdest")])

    cmd = ["rclone", "lsjson", f'--config={conf_path}', f"{drive_name}:{drive_base}", "--dirs-only" ] 

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
            [KeyboardButtonCallback("❌Nothing to show❌", data="mainmenu^pages")])
         return     

    data.sort(key=lambda x: x["Name"])  

    set_val("JSON_RESULT_DATA", data)
    data, next_offset, total= await get_list_drive_results_main(data)
    
    list_drive_main(data, menu, data_cb)

    if offset == 0 and total <= 10:
        menu.append(
            [KeyboardButtonCallback(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", data="mainmenu^pages")]) 
            
    else: 
        menu.append(
            [KeyboardButtonCallback(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", data="mainmenu^pages"),
             KeyboardButtonCallback("NEXT ⏩", data= f"next {next_offset} {data_back_cb}")
            ]) 
           
async def get_list_drive_results_main(data, max_results=10, offset=0):
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

def list_drive_main(result, menu=[], data_cb=""):
     folder = ""
     file= ""
     index= 0
     for i in result:
        path = i["Path"]
        path == path.strip()
        index= index + 1
        set_val(f"{index}", path)
        mime_type= i['MimeType']
        if mime_type == 'inode/directory': 
            file= "" 
            folder= "📁"
        menu.append(        
        [KeyboardButtonCallback(f"{folder} {file} {path}", f"mainmenu^{data_cb}^{index}")]
     )