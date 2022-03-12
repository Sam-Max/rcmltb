import logging
import os
from bot.core.get_vars import get_val
from bot.core.settings_leech_menu import settings_leech_menu
from bot.core.set_vars import set_val
from bot.uploaders.rclone_leech import rclone_downloader

torlog = logging.getLogger(__name__)

async def handle_setting_leech_menu_callback(client, callback_query):
    sender= callback_query.from_user.id
    data = callback_query.data
    cmd = data.split("^")
    mmes = callback_query.message
    base_dir= get_val("BASE_DIR")
    rclone_drive = get_val("DEF_RCLONE_DRIVE")

    if callback_query.data == "pages":
        await callback_query.answer()

    elif cmd[1] == "list_drive_leech_menu":
        set_val("BASE_DIR", "")
        base_dir = get_val("BASE_DIR")
        set_val("DEF_RCLONE_DRIVE", cmd[2])
        await settings_leech_menu(
            callback_query, 
            mmes, 
            edit=True,
            msg=f"Select folder or file that you want to leech\n\nPath:`{cmd[2]}:{base_dir}`", 
            drive_name= cmd[2], 
            submenu="list_drive", 
            data_cb="list_dir_leech_menu", 
            )     

    elif cmd[1] == "list_dir_leech_menu":
        rclone_drive = get_val("DEF_RCLONE_DRIVE")
        rclone_dir= get_val("BASE_DIR")
        path = get_val(cmd[2])
        logging.info("path: {}".format(path))
        rclone_dir +=  path +"/"
        set_val("BASE_DIR", rclone_dir)
        await settings_leech_menu(
            callback_query, 
            mmes, 
            edit=True, 
            msg=f"Select folder or file that you want to leech\n\nPath:`{rclone_drive}:{rclone_dir}`", 
            drive_base=rclone_dir, 
            drive_name= rclone_drive, 
            submenu="list_drive", 
            data_cb="list_dir_leech_menu", 
            )

    elif cmd[1] == "start_leech":
        path = get_val(cmd[2])
        origin_dir= get_val("BASE_DIR")
        origin_dir += path
        dest_dir = os.path.join(os.getcwd(), "Downloads")
        await rclone_downloader(client, mmes, sender, origin_dir, dest_dir, path= path)

    elif cmd[1] == "start_leech_folder":
        origin_dir= get_val("BASE_DIR")
        dest_dir = os.path.join(os.getcwd(), "Downloads", origin_dir)
        await rclone_downloader(client, mmes, sender, origin_dir, dest_dir, folder= True)

    elif cmd[1] == "selfdest":
        await callback_query.answer("Closed")
        await mmes.delete()