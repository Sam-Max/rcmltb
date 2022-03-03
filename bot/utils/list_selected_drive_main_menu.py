from telethon.tl.types import KeyboardButtonCallback
import asyncio
import json
import logging
from json.decoder import JSONDecodeError
from bot.core.set_vars import set_val

botlog = logging.getLogger(__name__)

async def list_selected_drive(
    query, 
    drive_base, 
    drive_name, 
    conf_path, 
    data_cb, 
    menu, 
    offset= 0, 
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
    except JSONDecodeError as e:
        logging.info(e)

    if data == []:
         menu.append(
            [KeyboardButtonCallback("❌Nothing to show❌", data="mainmenu^pages")])
         return     

    data.sort(key=lambda x: x["Name"])  

    set_val("JSON_RESULT_DATA", data)
    data, next_offset, total= await get_list_drive_results(data)
    
    list_drive(data, menu, data_cb)

    if offset == 0 and total <= 10:
        menu.append(
            [KeyboardButtonCallback(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", data="mainmenu^pages")]) 
            
    else: 
        menu.append(
            [KeyboardButtonCallback(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", data="mainmenu^pages"),
             KeyboardButtonCallback("NEXT ⏩", data= f"next {next_offset}")
            ]) 
           
async def get_list_drive_results(data, max_results=10, offset=0):
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

def list_drive(result, menu=[], data_cb=""):
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






