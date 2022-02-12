from telethon.tl.types import KeyboardButtonCallback
from bot.core.getVars import get_val
import asyncio
import json
import logging

log = logging.getLogger(__name__)
yes = "✅"
folder = "📁"


async def list_selected_drive(drive_base, drive_name, conf_path, rclone_dir, data_cb, menu):
    menu.append([KeyboardButtonCallback(f"{yes} Seleccione esta Carpeta", f"settings {data_cb} / )".encode("UTF-8"))])

    cmd = ["rclone", "lsjson", f'--config={conf_path}', f"{drive_name}:{drive_base}", "--dirs-only"]

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
            path == path.strip()
            log.info(path)
            log.info(rclone_dir)
            size = i["Size"]
            prev= ''   
            if len(path) <= 20 and size == -1:
                if path == rclone_dir:
                    prev= yes
                if " " in path:
                    continue    
                menu.append(
                    [KeyboardButtonCallback(f"{prev} {folder} {path}", f"settings {data_cb} {path}".encode("UTF-8"))])
    except Exception as e:
        log.info(e)
