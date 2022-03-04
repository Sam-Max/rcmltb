from bot.utils.get_rclone_conf import get_config
import os, configparser, logging
from pyrogram.types import InlineKeyboardMarkup
from pyrogram.types import InlineKeyboardButton

from bot.utils.list_selected_drive_leech_menu import list_selected_drive_leech

torlog = logging.getLogger(__name__)

TIMEOUT_SEC = 60

header = ""

async def settings_leech_menu(
    client,
    message, 
    drive_base="", 
    edit=False, 
    msg="", 
    drive_name="", 
    data_cb="", 
    submenu=None, 
    ):
    
    menu = []

    if submenu is None:
        path= os.path.join(os.getcwd(), "rclone.conf")
        conf = configparser.ConfigParser()
        conf.read(path)

        for j in conf.sections():
            if "team_drive" in list(conf[j]):
                menu.append(
                    [InlineKeyboardButton(f"{j} - TD", f"leechmenu^{data_cb}^{j}")]
                )
            else:
                menu.append(
                    [InlineKeyboardButton(f"{j} - ND", f"leechmenu^{data_cb}^{j}")]
                )

        menu.append(
            [InlineKeyboardButton("Close Menu", f"leechmenu^selfdest")]
        )

        if edit:
            await message.edit(header + msg, reply_markup= InlineKeyboardMarkup(menu))
        else:
            await message.reply(msg, reply_markup= InlineKeyboardMarkup(menu))

    elif submenu == "list_drive":
        conf_path = await get_config()

        await list_selected_drive_leech(
            drive_base, 
            drive_name, 
            conf_path, 
            menu, 
            data_cb,
            )    

        menu.append(
            [InlineKeyboardButton("Close Menu", f"leechmenu^selfdest")]

        )
        if edit:
            await message.edit(msg, parse_mode="md", reply_markup= InlineKeyboardMarkup(menu))
        else:
            await message.reply(header, parse_mode="md", reply_markup= InlineKeyboardMarkup(menu))