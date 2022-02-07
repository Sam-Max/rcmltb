import configparser
from telethon.tl.types import KeyboardButtonCallback
from bot.core.getVars import get_val
import asyncio
import json
import logging

log = logging.getLogger(__name__)
yes = "✅"


async def copy(e, header, origin_menu=True, destination_menu=False):
    menu = []

    if destination_menu:
        menu_drive_create(menu, "set_dir_dest")
        await e.edit(header, parse_mode="html", buttons=menu, link_preview=False)

    if origin_menu:
        menu_drive_create(menu, "set_dir_origin")
        await e.reply(header, parse_mode="html", buttons=menu, link_preview=False)


def menu_drive_create(menu, query):
    path = get_val("RCLONE_CONFIG")
    conf = configparser.ConfigParser()
    conf.read(path)


    for j in conf.sections():
        log.info(j)

        if "team_drive" in list(conf[j]):
            menu.append(
                [KeyboardButtonCallback(f"{j} - TD", f"copy {query} {j}")]
            )
        else:
            menu.append(
                [KeyboardButtonCallback(f"{j} - ND", f"copy {query} {j}")]
            )

    menu.append(
        [KeyboardButtonCallback("Cerrar Menu", f"copy close".encode("UTF-8"))]
    )


async def list_selected_drive(e, header, drive_name, drive_base, conf_path, query):
    menu = [[KeyboardButtonCallback(f"{yes} Seleccione esta Carpeta", "copy {} {}".format(query, "/"))]]

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
            if len(path) < 10:
                format_path = path.strip()
                menu.append(
                    [KeyboardButtonCallback(f"{format_path}", "copy {} {}".format(query, format_path))]
                )
    except:
        log.info("Error")
    menu.append(
        [KeyboardButtonCallback("Cerrar Menu", f"copy close".encode("UTF-8"))]
    )

    await e.edit(header, parse_mode="html", buttons=menu, link_preview=False)
