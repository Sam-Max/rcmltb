import os
from bot.core.get_vars import get_val
from bot.core.menus.menu_leech import settings_leech_menu
from bot.core.set_vars import set_val
from bot.uploaders.rclone.rclone_leech import RcloneLeech


async def handle_setting_leech_menu_callback(client, callback_query):
    chat_id = callback_query.message.chat.id
    data = callback_query.data
    cmd = data.split("^")
    mmes = callback_query.message
    base_dir= get_val("BASE_DIR")
    rclone_drive = get_val("DEFAULT_RCLONE_DRIVE")

    if callback_query.data == "pages":
        await callback_query.answer()

    elif cmd[1] == "list_drive_leech_menu":
        set_val("BASE_DIR", "")
        base_dir = get_val("BASE_DIR")
        set_val("DEFAULT_RCLONE_DRIVE", cmd[2])
        await settings_leech_menu(
            callback_query, 
            mmes, 
            edit=True,
            msg=f"Select folder or file that you want to leech\n\nPath:`{cmd[2]}:{base_dir}`", 
            drive_name= cmd[2], 
            submenu="list_drive", 
            data_cb="list_dir_leech_menu", 
            data_back_cb= "lchmenu"
            )     

    elif cmd[1] == "list_dir_leech_menu":
        rclone_drive = get_val("DEFAULT_RCLONE_DRIVE")
        rclone_dir= get_val("BASE_DIR")
        path = get_val(cmd[2])
        rclone_dir +=  path + "/"
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
            data_back_cb= "back"
            )

    elif cmd[1] == "start_leech_file":
        path = get_val(cmd[2])
        origin_dir= get_val("BASE_DIR")
        origin_dir += path
        dest_dir = os.path.join(os.getcwd(), "Downloads", origin_dir)
        rclone_leech= RcloneLeech(mmes, chat_id, origin_dir, dest_dir, path=path)
        await rclone_leech.leech()

    elif cmd[1] == "start_leech_folder":
        origin_dir= get_val("BASE_DIR")
        dest_dir = os.path.join(os.getcwd(), "Downloads", origin_dir)
        rclone_leech= RcloneLeech(mmes, chat_id, origin_dir, dest_dir, folder= True)
        await rclone_leech.leech()

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
        
        if rclone_dir == "":data_b_cb= "lchmenu"

        await settings_leech_menu(
            callback_query,
            mmes, 
            edit=True, 
            msg=f"Select folder where you want to store files\n\nPath:`{rclone_drive}:{rclone_dir}`", 
            drive_base=rclone_dir, 
            drive_name= rclone_drive, 
            submenu="list_drive", 
            data_cb="list_dir_leech_menu", 
            data_back_cb= data_b_cb
            )   

    elif cmd[1]== "lchmenu":
        await settings_leech_menu(
            callback_query, 
            mmes, 
            msg= "Select cloud where your files are stored",
            data_cb="list_drive_leech_menu",
            edit=True
            )     

    elif cmd[1] == "selfdest":
        await callback_query.answer("Closed")
        await mmes.delete()