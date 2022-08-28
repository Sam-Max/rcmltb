from bot.core.menus.menu_myfiles import myfiles_menu
from bot.core.menus.menu_myfiles_settings import settings_myfiles_menu
from bot.core.varholderwrap import get_val, set_val

async def handle_setting_myfiles_menu_callback(client, callback_query):
    query= callback_query
    data = query.data
    cmd = data.split("^")
    message = query.message
    base_dir= get_val("MYFILES_BASE_DIR")
    rclone_drive = get_val("RCLONE_DRIVE")

    if query.data == "pages":
        await query.answer()

    if cmd[1] == "list_drive_myfiles_menu":
             
        #Clean Menu
        set_val("MYFILES_BASE_DIR", "")
        base_dir= get_val("MYFILES_BASE_DIR")
             
        drive_name= cmd[2]     
        set_val("RCLONE_DRIVE", drive_name)
        await myfiles_menu(
            query, 
            message, 
            edit=True,
            msg=f"Your drive files are listed below\n\nPath:`{drive_name}:{base_dir}`", 
            drive_name= drive_name, 
            submenu="list_dir", 
            data_cb="list_dir_myfiles_menu", 
            data_back_cb= "myfiles_menu_back"
            )     

    elif cmd[1] == "list_dir_myfiles_menu":
        path = get_val(cmd[2])
        base_dir += path + "/"
        set_val("MYFILES_BASE_DIR", base_dir)
        await myfiles_menu(
            query, 
            message, 
            edit=True, 
            msg=f"Your drive files are listed below\n\nPath:`{rclone_drive}:{base_dir}`", 
            drive_base=base_dir, 
            drive_name= rclone_drive, 
            submenu="list_dir", 
            data_cb="list_dir_myfiles_menu", 
            data_back_cb= "myfiles_back"
            )

    elif cmd[1] == "start_file_actions":
        path = get_val(cmd[2])
        base_dir += path
        set_val("MYFILES_BASE_DIR", base_dir) 
        await settings_myfiles_menu(
            client, 
            message,
            msg= f"Path:`{rclone_drive}:{base_dir}`",
            drive_base= base_dir,
            edit=True, 
            submenu="myfiles_menu_setting",
            is_folder= False 
        )

    elif cmd[1] == "start_folder_actions":
        await settings_myfiles_menu(
            client, 
            message,
            msg= f"Path:`{rclone_drive}:{base_dir}`", 
            drive_base= base_dir,
            edit=True, 
            submenu="myfiles_menu_setting",
            is_folder= True 
        )

    # Handle back button
    elif cmd[1] == "myfiles_back":
        base_dir_split= base_dir.split("/")[:-2]
        base_dir_string = "" 
        for dir in base_dir_split: 
            base_dir_string += dir + "/"
        base_dir = base_dir_string
        set_val("MYFILES_BASE_DIR", base_dir)
        
        if len(base_dir) > 0: 
            data_b_cb= cmd[1]  
        else:
            data_b_cb= "myfiles_menu_back"

        await myfiles_menu(
            query,
            message, 
            msg=f"Path:`{rclone_drive}:{base_dir}`", 
            drive_base= base_dir, 
            drive_name= rclone_drive, 
            submenu="list_dir", 
            data_cb="list_dir_myfiles_menu", 
            edit=True, 
            data_back_cb= data_b_cb)   

    elif cmd[1]== "myfiles_menu_back":
        await myfiles_menu(
            query, 
            message, 
            msg= "Please select your drive to see files",
            submenu= "list_drive",
            data_cb= "list_drive_myfiles_menu",
            edit=True)     

    #Handling actions

    if cmd[1] == "delete_action":
        if cmd[2] == "folder":
            is_folder= True
        elif cmd[2] == "file":
            is_folder= False

        await settings_myfiles_menu(
            client, 
            message,
            drive_base= base_dir, 
            drive_name= rclone_drive, 
            edit=True, 
            submenu= "rclone_delete",
            is_folder= is_folder)

    elif cmd[1] == "size_action":
        await settings_myfiles_menu(
            client, 
            message,
            drive_base= base_dir, 
            drive_name= rclone_drive, 
            submenu= "rclone_size", 
            edit=True)

    if cmd[1] == "close":
        await query.answer("Closed")
        set_val("MYFILES_BASE_DIR", "")
        set_val("RCLONE_DRIVE", "")
        await message.delete()

    #Handling purge delete dialog

    if cmd[1]== "yes":
        if cmd[2] == "folder":
            is_folder= True
        elif cmd[2] == "file":
            is_folder= False

        await settings_myfiles_menu(
            client, 
            message,
            drive_base= base_dir, 
            drive_name= rclone_drive, 
            edit=True, 
            submenu= "yes",
            is_folder= is_folder)

    elif cmd[1]== "no":
        await query.answer("Closed") 
        set_val("MYFILES_BASE_DIR", "")
        await message.delete()