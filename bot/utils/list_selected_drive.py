from telethon.tl.types import KeyboardButtonCallback
from bot.core.getVars import get_val
import asyncio
import json
import logging

log = logging.getLogger(__name__)
yes = "✅"
folder = "📁"


async def list_selected_drive(drive_base, drive_name, conf_path, data_cb, menu):
    menu.append([KeyboardButtonCallback(f"{yes} Seleccione esta Carpeta", f"settings {data_cb} /)".encode("UTF-8"))])

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
            size = i["Size"]
            if len(path) < 10:
                if size == -1:
                    format_path = path.strip()
                    menu.append(
                        [KeyboardButtonCallback(f"{folder}{format_path}", f"settings {data_cb} {format_path}".encode("UTF-8"))])
    except:
        log.info("Error")
