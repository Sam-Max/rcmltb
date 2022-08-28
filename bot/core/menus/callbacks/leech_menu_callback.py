import os
from bot import DOWNLOAD_DIR, LOGGER
from bot.core.menus.menu_leech import leech_menu
from bot.core.varholderwrap import get_val, set_val
from bot.uploaders.rclone.rclone_leech import RcloneLeech


async def handle_leech_menu_callback(client, callback_query):
    query= callback_query
    chat_id = query.message.chat.id
    data = query.data
    cmd = data.split("^")
    message = query.message
    base_dir= get_val("LEECH_BASE_DIR")
    rclone_drive = get_val("RCLONE_DRIVE")
    is_zip = False
    extract = False

    msg= 'Select folder or file that you want to leech\n'
    if get_val('IS_ZIP'):
        msg= 'Select file that you want to zip\n' 
        is_zip= True
        
    if get_val('EXTRACT'):
        msg= 'Select file that you want to extract\n'
        extract= True

    if data == "pages":
        await query.answer()

    if cmd[1] == "list_drive_leech_menu":
             
        #reset menu
        set_val("LEECH_BASE_DIR", "")
        base_dir= get_val("LEECH_BASE_DIR")

        drive_name= cmd[2]
        set_val("RCLONE_DRIVE", drive_name)
        await leech_menu(
            query, 
            message, 
            msg=f"{msg}\nPath:`{drive_name}:{base_dir}`", 
            drive_name= drive_name, 
            submenu="list_dir", 
            data_cb="list_dir_leech_menu",
            edit=True, 
            data_back_cb= "leech_menu_back"
            )     

    elif cmd[1] == "list_dir_leech_menu":
        path = get_val(cmd[2])
        base_dir += path + "/"
        set_val("LEECH_BASE_DIR", base_dir)
        await leech_menu(
            query, 
            message, 
            edit=True, 
            msg=f"{msg}\nPath:`{rclone_drive}:{base_dir}`", 
            drive_base= base_dir, 
            drive_name= rclone_drive, 
            submenu="list_dir", 
            data_cb="list_dir_leech_menu", 
            data_back_cb= "leech_back"
            )

    elif cmd[1] == "start_leech_file":
        path = get_val(cmd[2])
        base_dir += path
        dest_dir = f'{DOWNLOAD_DIR}{path}'
        rclone_leech= RcloneLeech(message, chat_id, base_dir, dest_dir, path, isZip=is_zip, extract=extract)
        await rclone_leech.execute()

    elif cmd[1] == "start_leech_folder":
        dest_dir = f'{DOWNLOAD_DIR}{base_dir}'
        rclone_leech= RcloneLeech(message, chat_id, base_dir, dest_dir, isZip=is_zip, extract=extract, folder=True)
        await rclone_leech.execute()

    elif cmd[1] == "leech_back":
        base_dir_split= base_dir.split("/")[:-2]
        base_dir_string = "" 
        for dir in base_dir_split: 
            base_dir_string += dir + "/"
        base_dir = base_dir_string
        set_val("LEECH_BASE_DIR", base_dir)
        
        if len(base_dir) > 0: 
            data_b_cb= cmd[1]  
        else:
            data_b_cb= "leech_menu_back"

        await leech_menu(
            query,
            message, 
            edit=True, 
            msg=f"{msg}\nPath:`{rclone_drive}:{base_dir}`", 
            drive_base= base_dir, 
            drive_name= rclone_drive, 
            submenu="list_dir", 
            data_cb="list_dir_leech_menu", 
            data_back_cb= data_b_cb
            )   

    elif cmd[1]== "leech_menu_back":
        await leech_menu(
            query, 
            message, 
            msg= "Select cloud where your files are stored",
            submenu= "list_drive",
            data_cb="list_drive_leech_menu",
            edit=True)     

    elif cmd[1] == "close":
        await query.answer("Closed")
        set_val("LEECH_BASE_DIR", "")
        await message.delete()