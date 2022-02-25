from telethon.tl.types import KeyboardButtonCallback
from bot.utils.list_selected_drive_copy_menu import list_selected_drive_copy
import os, configparser, logging

torlog = logging.getLogger(__name__)

TIMEOUT_SEC = 60

header = ""

async def handle_settings_copy_menu(
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
        #path = get_val("RCLONE_CONFIG")
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
            [KeyboardButtonCallback("Cerrar Menu", f"copymenu^selfdest")]
        )

        if edit:
            rmess = await mmes.edit(header + msg,
                                 parse_mode="html", buttons=menu, link_preview=False)
        else:
            rmess = await query.reply(msg,
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
            [KeyboardButtonCallback("Cerrar Menu", f"copymenu^selfdest")]

        )
        if edit:
            rmess = await mmes.edit(msg,
                                 parse_mode="md", buttons=menu, link_preview=False)
        else:
            rmess = await query.reply(header,
                                  parse_mode="md", buttons=menu, link_preview=False)

######################################################################                                  


async def get_config():
    config = os.path.join(os.getcwd(), "rclone.conf")
    if isinstance(config, str):
        if os.path.exists(config):
            return config

    return None
