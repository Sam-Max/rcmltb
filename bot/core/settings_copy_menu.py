from telethon.tl.types import KeyboardButtonCallback
from bot.utils.get_rclone_conf import get_config
import os, configparser, logging
from telethon.tl.types import KeyboardButtonCallback
import asyncio
import json
import logging
from json.decoder import JSONDecodeError
from bot.core.set_vars import set_val

torlog = logging.getLogger(__name__)

header = ""

async def settings_copy_menu(
    query, 
    mmes="",
    drive_base="", 
    edit=False, 
    msg="", 
    drive_name="", 
    data_cb="", 
    submenu=None, 
    is_second_menu= False, 
    ):
    
    menu = []

    if submenu == "rclone_menu_copy":
        path= os.path.join(os.getcwd(), "rclone.conf")
        conf = configparser.ConfigParser()
        conf.read(path)

        for j in conf.sections():
            if "team_drive" in list(conf[j]):
                menu.append(
                    [KeyboardButtonCallback(f"{j} - TD", f"copymenu^{data_cb}^{j}")]
                )
            else:
                menu.append(
                    [KeyboardButtonCallback(f"{j} - ND", f"copymenu^{data_cb}^{j}")]
                )

        menu.append(
            [KeyboardButtonCallback("Close Menu", f"copymenu^selfdest")]
        )

        if edit:
            await mmes.edit(header + msg,
                                 parse_mode="html", buttons=menu, link_preview=False)
        else:
           await query.reply(msg,
                                  parse_mode="html", buttons=menu, link_preview=False)

    elif submenu == "list_drive":
        conf_path = await get_config()

        await list_selected_drive_copy(
            query, 
            drive_base, 
            drive_name, 
            conf_path, 
            menu, 
            callback=data_cb,
            is_second_menu= is_second_menu, 
            )    

        menu.append(
            [KeyboardButtonCallback("Close Menu", f"copymenu^selfdest")]

        )
        if edit:
            await mmes.edit(msg,
                                 parse_mode="md", buttons=menu, link_preview=False)
        else:
            await query.reply(header,
                                  parse_mode="md", buttons=menu, link_preview=False)

async def list_selected_drive_copy(
    query, 
    drive_base, 
    drive_name, 
    conf_path, 
    menu, 
    callback= "",
    offset= 0, 
    is_second_menu= False, 
    ):
    
    if is_second_menu:
         menu.append([KeyboardButtonCallback(f" ✅ Select this folder", f"copymenu^start_copy")])
    else:
         menu.append([KeyboardButtonCallback(f" ✅ Select this folder", f"copymenu^rclone_menu_copy^jhjh^False")])
    
    if is_second_menu:
         cmd = ["rclone", "lsjson", f'--config={conf_path}', f"{drive_name}:{drive_base}", "--dirs-only"] 
    else:
         cmd = ["rclone", "lsjson", f'--config={conf_path}', f"{drive_name}:{drive_base}"] 

    process = await asyncio.create_subprocess_exec(
    *cmd,
    stdout=asyncio.subprocess.PIPE
    )

    stdout, _ = await process.communicate()
    stdout = stdout.decode().strip()

    try:
        data = json.loads(stdout)
    except JSONDecodeError as e:
        logging.info(e)
        return

    if data == []:
         menu.append(
            [KeyboardButtonCallback("❌Nothing to show❌", data="copymenu^pages")])
         return 

    if is_second_menu:
        data.sort(key=lambda x: x["Name"]) 
    else:
        data.sort(key=lambda x: x["Size"])        

    set_val("JSON_RESULT_DATA", data)

    data, next_offset, total= await get_list_drive_results_copy(data)
    
    list_drive_copy(
        result= data, 
        menu= menu, 
        callback=callback
    )

    if offset == 0 and total <= 10:
        menu.append(
            [KeyboardButtonCallback(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", data="copymenu^pages")]) 
    else: 
        menu.append(
            [KeyboardButtonCallback(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", data="copymenu^pages"),
             KeyboardButtonCallback("NEXT ⏩", data= f"n_copy {next_offset} {is_second_menu}")
            ]) 
           
async def get_list_drive_results_copy(data, max_results=10, offset=0):
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

def list_drive_copy(
    result, 
    menu=[], 
    callback="", 
    ):
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
            [KeyboardButtonCallback(f"{folder} {file} {path}", f"copymenu^{callback}^{index}")]
        )    
        else:
            file= "🗄" 
            folder= ""
            menu.append(        
            [KeyboardButtonCallback(f"{folder} {file} {path}", f"copymenu^rclone_menu_copy^{index}^True")]
        )