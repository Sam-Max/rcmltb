from telethon.tl.types import KeyboardButtonCallback
import asyncio
import json
import logging
from json.decoder import JSONDecodeError
from bot import SessionVars

botlog = logging.getLogger(__name__)

async def list_selected_drive_copy(
    query, 
    drive_base, 
    drive_name, 
    conf_path, 
    rclone_dir, 
    menu, 
    callback= "",
    offset= 0, 
    is_second_menu= False, 
    is_dest_drive=False
    ):
    
    if is_second_menu:
         menu.append([KeyboardButtonCallback(f" ✅ Seleccione esta Carpeta", f"copymenu^start_copy")])
    else:
         menu.append([KeyboardButtonCallback(f" ✅ Seleccione esta Carpeta", f"copymenu^rclone_menu_copy")])
    
    #botlog.info(f"{drive_name}:{drive_base}")
    botlog.info(f"CONF_PATH: {conf_path}")

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

    #logging.info(data)
    if data == []:
         menu.append(
            [KeyboardButtonCallback(f"🗓 Nada que mostrar", data="setting pages")])
         return 
    SessionVars.update_var("JSON_RESULT_DATA", data)
    data, next_offset, total= await get_list_drive_results_copy(data)
    
    list_drive_copy(
        result= data, 
        rclone_dir= rclone_dir,
        menu= menu, 
        callback=callback
    )

    if offset == 0 and total <= 10:
        menu.append(
            [KeyboardButtonCallback(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", data="setting pages")]) 
    else: 
        menu.append(
            [KeyboardButtonCallback(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", data="setting pages"),
             KeyboardButtonCallback("NEXT ⏩", data= f"next_copy {next_offset} {is_second_menu}")
            ]) 
           
async def get_list_drive_results_copy(data, max_results=10, offset=0):
    total = len(data)
    logging.info(f"Total: {total}")

    botlog.info(f"OFFSET: {offset}")

    next_offset = offset + max_results
    
    #if next_offset >= total:
        #next_offset = -2

    #if next_offset < 0:
        #next_offset = -1    

    botlog.info(f"NEXT_OFFSET: {next_offset}")
    
    data = await list_range(offset, max_results, data)
    return data, next_offset, total    

async def list_range(offset, max_results, data):
    # this handles both negative offsets and offsets larger than list length
    start = offset % len(data)
    end = (start + max_results) % len(data)
    if end > start:
        return data[start:end]
    return data[start:] + data[:end]             

def list_drive_copy(
    result, 
    rclone_dir="",
    menu=[], 
    callback="", 
    ):

     folder = ""
     file= ""
     for i in result:
        path = i["Path"]
        path == path.strip()
        mime_type= i['MimeType']
        if len(path) <= 30: 
                #selected folder or zip
                if path == rclone_dir: 
                    folder= ""
                    mime_type= ""
                if mime_type == 'inode/directory': 
                    file= "" 
                    folder= "📁"
                    menu.append(  
                    [KeyboardButtonCallback(f"{folder} {file} {path}", f"copymenu^{callback}^{path}")]
                    )    
                else:
                    file= "🗄" 
                    folder= ""
                    menu.append(        
                    [KeyboardButtonCallback(f"{folder} {file} {path}", f"copymenu^rclone_menu_copy")])
                botlog.info(path)
                






