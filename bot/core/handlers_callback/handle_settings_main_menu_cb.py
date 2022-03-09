import logging
from bot.core.get_vars import get_val
from bot.core.settings_main_menu import settings_main_menu
from bot.core.set_vars import set_val

torlog = logging.getLogger(__name__)

async def handle_setting_main_menu_callback(callback_query):
    data = callback_query.data.decode()
    cmd = data.split("^")
    mmes = await callback_query.get_message()
    base_dir= get_val("BASE_DIR")
    rclone_drive = get_val("DEF_RCLONE_DRIVE")

    if callback_query.data == "pages":
        await callback_query.answer()

    elif cmd[1] == "list_drive_main_menu":
        set_val("BASE_DIR", "")
        base_dir = get_val("BASE_DIR")
        set_val("DEF_RCLONE_DRIVE", cmd[2])
        await settings_main_menu(
            callback_query, 
            mmes, 
            edit=True,
            msg=f"Select folder where you want to store files\n\nPath:`{cmd[2]}:{base_dir}`", 
            drive_name= cmd[2], 
            submenu="list_drive", 
            data_cb="list_dir_main_menu", 
            )     

    elif cmd[1] == "list_dir_main_menu":
        rclone_drive = get_val("DEF_RCLONE_DRIVE")
        rclone_dir= get_val("BASE_DIR")
        path = get_val(cmd[2])
        logging.info("path: {}".format(path))
        rclone_dir +=  path +"/"
        set_val("BASE_DIR", rclone_dir)
        await settings_main_menu(
            callback_query, mmes, 
            edit=True, 
            msg=f"Select folder where you want to store files\n\nPath:`{rclone_drive}:{rclone_dir}`", 
            drive_base=rclone_dir, 
            drive_name= rclone_drive, 
            submenu="list_drive", 
            data_cb="list_dir_main_menu", 
            )

    # close menu
    elif cmd[1] == "selfdest":
        await callback_query.answer("Closed")
        await callback_query.delete()