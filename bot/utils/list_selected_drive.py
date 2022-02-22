from telethon.tl.types import KeyboardButtonCallback
import asyncio
import json
import logging
from bot import SessionVars

botlog = logging.getLogger(__name__)

#"--dirs-only"

async def list_selected_drive(query, drive_base, drive_name, conf_path, rclone_dir, data_cb, menu, offset= 0, is_main_m= True):
    menu.append([KeyboardButtonCallback(f" ✅ Seleccione esta Carpeta", f"settings selfdest".encode("UTF-8"))])

    #botlog.info(f"{drive_name}:{drive_base}")

    if is_main_m:
        cmd = ["rclone", "lsjson", f'--config={conf_path}', f"{drive_name}:{drive_base}", "--dirs-only" ] 
    else:
        cmd = ["rclone", "lsjson", f'--config={conf_path}', f"{drive_name}:{drive_base}"] 

    # piping only stdout
    process = await asyncio.create_subprocess_exec(
    *cmd,
    stdout=asyncio.subprocess.PIPE
    )

    stdout, _ = await process.communicate()
    stdout = stdout.decode().strip()
    data = json.loads(stdout)
    #logging.info(data)
    if data == []:
         return await query.answer("Nada que mostrar", alert=True)
    SessionVars.update_var("DRIVE_RES_DATA", data)
    result, next_offset, total= await get_list_drive_results(data)
    
    list_drive(result, rclone_dir, menu, data_cb)

    if offset == 0:
        menu.append(
            [KeyboardButtonCallback(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", data="setting pages"),
             KeyboardButtonCallback("NEXT ⏩", data= f"next {next_offset}".encode("UTF-8"))
            ]) 

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
                else:
                    file= "🗄" 
                    folder= ""
                botlog.info(path)
                menu.append(        
                [KeyboardButtonCallback(f"{folder} {file} {path}", f"settings^{data_cb}^{path}")]
                )

async def get_list_drive_results(data, max_results=10, offset=0):
    total = len(data)
    #logging.info(total)
    botlog.info(f"OFFSET: {offset}")
    next_offset = offset + max_results
    botlog.info(f"NEXT_OFFSET: {next_offset}")

    if next_offset > total:
        next_offset = ''
    
    result = await list_range(offset, max_results, data)

    return result, next_offset, total

async def list_range(offset, max_results, data):
    # this handles both negative offsets and offsets larger than list length
    start = offset % len(data)
    #logging.info(start)
    end = (start + max_results) % len(data)
    #logging.info(start + max_results)
    #logging.info(end)
    if len(data) < max_results:
        return data 
    if end > start:
        return data[start:end]
    return data[start:] + data[:end] 


