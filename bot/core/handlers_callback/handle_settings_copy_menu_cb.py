from bot.core.get_vars import get_val
from bot.core.set_vars import set_val
from bot.core.settings_copy_menu import settings_copy_menu
from bot.uploaders.rclone_copy import rclone_copy_transfer
import logging
from bot.utils.get_rclone_conf import get_config

torlog = logging.getLogger(__name__)



async def handle_setting_copy_menu_callback(callback_query):
    conf_path = await get_config()
    data = callback_query.data.decode()
    cmd = data.split("^")
    mmes = await callback_query.get_message()

    if callback_query.data == "pages":
        await callback_query.answer()

    #1 --- rclone_menu_copy    

    if cmd[1] == "list_drive_origin":
        set_val("ORIGIN_DRIVE", cmd[2])
        origin_drive= get_val("ORIGIN_DRIVE")
        set_val("ORIGIN_DIR", "/")
        await settings_copy_menu(
            query= callback_query, 
            mmes= mmes, 
            edit=True,
            msg= f'Select file/folder which you want to copy\n\nPath: `{origin_drive}`', 
            drive_name= cmd[2],
            submenu="list_drive", 
            data_cb="list_dir_origin",
            is_second_menu=False
           )

    elif cmd[1] == "list_dir_origin":
        origin_drive = get_val("ORIGIN_DRIVE")
        origin_dir= get_val("ORIGIN_DIR")
        path = get_val(cmd[2])
        logging.info("path: {}".format(path))
        rclone_dir= origin_dir + path + "/"
        set_val("ORIGIN_DIR", rclone_dir)
        await settings_copy_menu(
             callback_query,
             mmes, 
             edit=True, 
             msg=f"Select file/folder which you want to copy\n\nPath:`{origin_drive}:{rclone_dir}`", 
             drive_base=rclone_dir, 
             drive_name= origin_drive,
             data_cb="list_dir_origin",
             submenu="list_drive",
             is_second_menu= False
             )

    elif cmd[1] == "rclone_menu_copy":
        ####---True if click on a file, False if click on folder---####
        if cmd[3] == "True": 
            origin_dir= get_val("ORIGIN_DIR")
            path= get_val(cmd[2])
            rclone_dir= origin_dir + path + "/"
            set_val("ORIGIN_DIR", rclone_dir)
            await settings_copy_menu(
                callback_query,
                mmes, 
                edit=True, 
                msg=f"Select cloud where to copy files", 
                submenu="rclone_menu_copy", 
                data_cb="list_drive_dest"
                )
        else:
            await settings_copy_menu(
                callback_query,
                mmes, 
                edit=True, 
                msg=f"Select cloud where to copy files", 
                submenu="rclone_menu_copy", 
                data_cb="list_drive_dest"
                )                               
  
    elif cmd[1] == "list_drive_dest":
        set_val("DEST_DRIVE", cmd[2])
        dest_drive= get_val("DEST_DRIVE")
        set_val("DEST_DIR", "/")
        await settings_copy_menu(
            callback_query, 
            mmes, 
            edit=True, 
            msg=f'Select folder where you want to copy\n\nPath: `{dest_drive}`', 
            drive_name= cmd[2],
            submenu="list_drive", 
            data_cb="list_dir_dest",
            is_second_menu=True
            )

    elif cmd[1] == "list_dir_dest":
        dest_drive = get_val("DEST_DRIVE")
        dest_dir= get_val("DEST_DIR")
        path= get_val(cmd[2])
        rclone_dir= dest_dir + path + "/"
        set_val("DEST_DIR", rclone_dir)
        await settings_copy_menu(
             callback_query,
             mmes, 
             edit=True, 
             msg=f"Select folder where you want to copy\n\nPath:`{dest_drive}:{rclone_dir}`", 
             drive_base=rclone_dir, 
             drive_name= dest_drive,
             data_cb="list_dir_dest",
             submenu="list_drive", 
             is_second_menu= True
             )        
 
    elif cmd[1] == "start_copy":
        origin_dir = get_val("ORIGIN_DIR")
        origin_dir= origin_dir.split("/")[-2] + "/"
        rclone_dir= get_val("DEST_DIR")
        set_val("DEST_DIR", rclone_dir + origin_dir)
        await rclone_copy_transfer(callback_query, conf_path)                               

    # close menu
    elif cmd[1] == "selfdest":
        await callback_query.answer("Closed")
        await callback_query.delete()
