import logging
from bot.core.get_vars import get_val
from bot.core.menus.menu_mirrorset import settings_mirrorset_menu
from bot.core.set_vars import set_val

log = logging.getLogger(__name__)

async def handle_setting_mirroset_callback(callback_query):
    data = callback_query.data.decode()
    cmd = data.split("^")
    mmes = await callback_query.get_message()
    base_dir= get_val("BASE_DIR")
    rclone_drive = get_val("DEFAULT_RCLONE_DRIVE")

    if callback_query.data == "pages":
        await callback_query.answer()

    elif cmd[1] == "list_drive_mirrorset_menu":
        set_val("BASE_DIR", "")
        base_dir = get_val("BASE_DIR")
        set_val("DEFAULT_RCLONE_DRIVE", cmd[2])
        await settings_mirrorset_menu(
            callback_query, 
            mmes, 
            edit=True,
            msg=f"Select folder where you want to store files\n\nPath:`{cmd[2]}:{base_dir}`", 
            drive_name= cmd[2], 
            submenu="list_drive", 
            data_cb="list_dir_mirrorset_menu", 
            data_back_cb= "mirrorsetmenu"
            )     

    elif cmd[1] == "list_dir_mirrorset_menu":
        rclone_drive = get_val("DEFAULT_RCLONE_DRIVE")
        rclone_dir= get_val("BASE_DIR")
        path = get_val(cmd[2])
        rclone_dir += path + "/"
        set_val("BASE_DIR", rclone_dir)
        await settings_mirrorset_menu(
            callback_query, 
            mmes, 
            edit=True, 
            msg=f"Select folder where you want to store files\n\nPath:`{rclone_drive}:{rclone_dir}`", 
            drive_base=rclone_dir, 
            drive_name= rclone_drive, 
            submenu="list_drive", 
            data_cb="list_dir_mirrorset_menu", 
            data_back_cb= "back"
            )

    elif cmd[1] == "back":
        data_b_cb= "back"
        rclone_drive = get_val("DEFAULT_RCLONE_DRIVE")
        rclone_dir= get_val("BASE_DIR")
        rclone_dir_split= rclone_dir.split("/")
        rclone_dir_split = rclone_dir_split[:-2]
        rclone_dir_string = "" 
        for dir in rclone_dir_split: 
            rclone_dir_string += dir + "/"
        rclone_dir = rclone_dir_string
        set_val("BASE_DIR", rclone_dir)
        
        if rclone_dir_string == "": data_b_cb= "mirrorsetmenu"

        await settings_mirrorset_menu(
                    callback_query,
                    mmes, 
                    edit=True, 
                    msg=f"Select folder where you want to store files\n\nPath:`{rclone_drive}:{rclone_dir}`", 
                    drive_base=rclone_dir, 
                    drive_name= rclone_drive, 
                    submenu="list_drive", 
                    data_cb="list_dir_mirrorset_menu", 
                    data_back_cb= data_b_cb
                    ) 

    elif cmd[1]== "mirrorsetmenu":
         await settings_mirrorset_menu(callback_query, mmes= mmes, edit=True)                

    elif cmd[1] == "selfdest":
        await callback_query.answer("Closed")
        await callback_query.delete()