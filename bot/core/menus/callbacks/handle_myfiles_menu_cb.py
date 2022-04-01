import logging
from bot.core.get_vars import get_val
from bot.core.menus.menu_myfiles import myfiles_menu
from bot.core.menus.menu_myfiles_settings import settings_myfiles_menu
from bot.core.set_vars import set_val

async def handle_setting_myfiles_menu_callback(client, callback_query):
    data = callback_query.data
    cmd = data.split("^")
    mmes = callback_query.message
    base_dir= get_val("BASE_DIR")
    rclone_drive = get_val("DEF_RCLONE_DRIVE")

    if callback_query.data == "pages":
        await callback_query.answer()

    elif cmd[1] == "list_drive_myfiles_menu":
        set_val("BASE_DIR", "")     
        base_dir = get_val("BASE_DIR")
        set_val("DEF_RCLONE_DRIVE", cmd[2])
        await myfiles_menu(
            callback_query, 
            mmes, 
            edit=True,
            msg=f"Your drive files are listed below\n\nPath:`{cmd[2]}:{base_dir}`", 
            drive_name= cmd[2], 
            submenu="list_drive", 
            data_cb="list_dir_myfiles_menu", 
            data_back_cb= "lchmenu"
            )     

    elif cmd[1] == "list_dir_myfiles_menu":
        rclone_drive = get_val("DEF_RCLONE_DRIVE")
        rclone_dir= get_val("BASE_DIR")
        path = get_val(cmd[2])
        logging.info("path: {}".format(path))
        rclone_dir +=  path +"/"
        set_val("BASE_DIR", rclone_dir)
        await myfiles_menu(
            callback_query, 
            mmes, 
            edit=True, 
            msg=f"Your drive files are listed below\n\nPath:`{rclone_drive}:{rclone_dir}`", 
            drive_base=rclone_dir, 
            drive_name= rclone_drive, 
            submenu="list_drive", 
            data_cb="list_dir_myfiles_menu", 
            data_back_cb= "back"
            )

    elif cmd[1] == "start_file_actions":
        rclone_drive = get_val("DEF_RCLONE_DRIVE")
        path = get_val(cmd[2])
        base_dir = get_val("BASE_DIR")
        base_dir += path
        set_val("BASE_DIR", base_dir) 
        await settings_myfiles_menu(
            client, 
            mmes,
            base_dir,
            msg= f"Path:`{rclone_drive}:{base_dir}`", 
            edit=True, 
            submenu=None,
            is_folder= False 
        )

    elif cmd[1] == "start_folder_actions":
        rclone_drive = get_val("DEF_RCLONE_DRIVE")
        base_dir = get_val("BASE_DIR")
        await settings_myfiles_menu(
            client, 
            mmes,
            base_dir,
            msg= f"Path:`{rclone_drive}:{base_dir}`", 
            edit=True, 
            submenu=None, 
            is_folder= True 
        )

    #Handling actions menu
    elif cmd[1] == "rename_action":
        pass
    
    elif cmd[1] == "delete_action":
        rclone_drive = get_val("DEF_RCLONE_DRIVE")
        rclone_dir= get_val("BASE_DIR")
        
        if cmd[2] == "folder":
            is_folder= True
        
        if cmd[2] == "file":
            is_folder= False
        
        await settings_myfiles_menu(
            client= client, 
            message= mmes,
            drive_base= rclone_dir, 
            drive_name= rclone_drive, 
            edit=True, 
            submenu= "rclone_delete",
            is_folder= is_folder 
        )

    elif cmd[1] == "size_action":
        rclone_drive = get_val("DEF_RCLONE_DRIVE")
        rclone_dir= get_val("BASE_DIR")
        await settings_myfiles_menu(
            client= client, 
            message= mmes,
            drive_base= rclone_dir, 
            drive_name= rclone_drive, 
            edit=True, 
            submenu= "rclone_size", 
        )

    #Close button    
    elif cmd[1] == "selfdest":
        await callback_query.answer("Closed")
        await mmes.delete()

    #Handling purge delete dialog
    elif cmd[1]== "yes":
        rclone_drive = get_val("DEF_RCLONE_DRIVE")
        rclone_dir= get_val("BASE_DIR")

        if cmd[2] == "folder":
            is_folder= True
        
        if cmd[2] == "file":
            is_folder= False

        await settings_myfiles_menu(
            client= client, 
            message= mmes,
            drive_base= rclone_dir, 
            drive_name= rclone_drive, 
            edit=True, 
            submenu= "yes",
            is_folder= is_folder
        )

    elif cmd[1]== "no":
        rclone_drive = get_val("DEF_RCLONE_DRIVE")
        rclone_dir= get_val("BASE_DIR")
        await settings_myfiles_menu(
            client, 
            mmes,
            msg= "Actions Menu", 
            edit=True, 
            submenu=None, 
        )