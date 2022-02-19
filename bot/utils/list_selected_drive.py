from telethon.tl.types import KeyboardButtonCallback
from bot.core.getVars import get_val
import asyncio
import json
import logging

log = logging.getLogger(__name__)
yes = "✅"
folder = "📁"

async def list_selected_drive(drive_base, drive_name, conf_path, rclone_dir, data_cb, menu, is_main_m= True):
    menu.append([KeyboardButtonCallback(f"{yes} Seleccione esta Carpeta", f"settings selfdest".encode("UTF-8"))])

    logging.info(f"{drive_name}:{drive_base}")

    if is_main_m:
        cmd = ["rclone", "lsjson", f'--config={conf_path}', f"{drive_name}:{drive_base}", "--dirs-only"]   
    else:
        cmd = ["rclone", "lsjson", f'--config={conf_path}', f"{drive_name}:{drive_base}"] 

    # piping only stdout
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE
    )

    stdout, _ = await process.communicate()
    stdout = stdout.decode().strip()

    try:
        data = json.loads(stdout)
        for i in data:
            path = i["Path"]
            #logging.info(path)
            path == path.strip()
            mime_type= i['MimeType']
            folder1= folder
            zip= ""
            if len(path) <= 20: 
                if path == rclone_dir: #selected folder or zip
                    folder1= ""
                    mime_type= ""
                    zip= ""
                if mime_type == 'application/zip' or mime_type == 'application/x-rar':  
                    zip= "🗄"  
                    folder1= ""
                if " " in path:
                    continue    
                menu.append(
                    [KeyboardButtonCallback(f"{folder1} {zip} {path}", f"settings {data_cb} {path}".encode("UTF-8"))])
    except Exception as e:
        log.info(e)
