from telethon.tl.types import KeyboardButtonCallback
import asyncio
import json
import logging
from json.decoder import JSONDecodeError
from bot import SessionVars

botlog = logging.getLogger(__name__)

async def list_selected_drive(query, drive_base, drive_name, conf_path, rclone_dir, data_cb, menu, offset= 0, is_main_m= True):
    menu.append([KeyboardButtonCallback(f" ✅ Seleccione esta Carpeta", f"mainmenu^selfdest")])

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
            [KeyboardButtonCallback(f"🗓 Nada que mostrar", data="setting pages")])
         return 
    SessionVars.update_var("JSON_RESULT_DATA", data)
    data, next_offset, total= await get_list_drive_results(data)
    
    list_drive(data, rclone_dir, menu, data_cb)

    if offset == 0 and total <= 10:
        menu.append(
            [KeyboardButtonCallback(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", data="setting pages")]) 
            
    else: 
        menu.append(
            [KeyboardButtonCallback(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", data="setting pages"),
             KeyboardButtonCallback("NEXT ⏩", data= f"next {next_offset}".encode("UTF-8"))
            ]) 
           
async def get_list_drive_results(data, max_results=10, offset=0):
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

def list_drive(result, rclone_dir="", menu=[], data_cb=""):
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
                botlog.info(path)
                menu.append(        
                [KeyboardButtonCallback(f"{folder} {file} {path}", f"mainmenu^{data_cb}^{path}")])






