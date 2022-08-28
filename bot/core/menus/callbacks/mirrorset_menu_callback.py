from bot.core.menus.menu_mirrorset import mirrorset_menu
from bot.core.varholderwrap import get_val, set_val


async def handle_setting_mirroset_callback(callback_query):
    query= callback_query
    data = query.data.decode()
    cmd = data.split("^")
    message = await query.get_message()
    base_dir= get_val("MIRRORSET_BASE_DIR")
    rclone_drive = get_val("RCLONE_MIRRORSET_DRIVE")

    if query.data == "pages":
        await query.answer()

    elif cmd[1] == "list_drive_mirrorset_menu":
        drive_name= cmd[2]
        
        #reset menu
        set_val("MIRRORSET_BASE_DIR", "")
        base_dir= get_val("MIRRORSET_BASE_DIR")

        set_val("RCLONE_MIRRORSET_DRIVE", drive_name)
        await mirrorset_menu(
            query, 
            message, 
            edit=True,
            msg=f"Select folder where you want to store files\n\nPath:`{drive_name}:{base_dir}`", 
            drive_name= drive_name, 
            submenu="list_dir", 
            data_cb="list_dir_mirrorset_menu", 
            data_back_cb= "mirrorset_menu_back"
            )     

    elif cmd[1] == "list_dir_mirrorset_menu":
        path = get_val(cmd[2])
        base_dir += path + "/"
        set_val("MIRRORSET_BASE_DIR", base_dir)
        await mirrorset_menu(
            query, 
            message, 
            edit=True, 
            msg=f"Select folder where you want to store files\n\nPath:`{rclone_drive}:{base_dir}`", 
            drive_base=base_dir, 
            drive_name= rclone_drive, 
            submenu="list_dir", 
            data_cb="list_dir_mirrorset_menu", 
            data_back_cb= "mirrorset_back"
            )

    elif cmd[1] == "mirrorset_back":
        base_dir_split= base_dir.split("/")[:-2]
        base_dir_string = "" 
        for dir in base_dir_split: 
            base_dir_string += dir + "/"
        base_dir = base_dir_string
        set_val("MIRRORSET_BASE_DIR", base_dir)
        
        if len(base_dir) > 0: 
            data_b_cb= cmd[1]  
        else:
            data_b_cb= "mirrorset_menu_back"

        await mirrorset_menu(
            query,
            message, 
            msg=f"Select folder where you want to store files\n\nPath:`{rclone_drive}:{base_dir}`", 
            drive_base=base_dir, 
            drive_name= rclone_drive, 
            submenu="list_dir", 
            data_cb="list_dir_mirrorset_menu", 
            edit=True,
            data_back_cb= data_b_cb
            ) 

    elif cmd[1]== "mirrorset_menu_back":
         await mirrorset_menu(
            query, 
            message, 
            msg= f"Select cloud where you want to upload file\n\nPath:`{rclone_drive}:{base_dir}`",
            submenu="list_drive",
            edit=True)                

    elif cmd[1] == "close":
        await callback_query.answer("Closed")
        await callback_query.delete()