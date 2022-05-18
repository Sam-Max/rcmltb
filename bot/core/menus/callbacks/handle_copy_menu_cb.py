from bot import GLOBAL_RC_INST
from bot.core.get_vars import get_val
from bot.core.menus.menu_copy import settings_copy_menu
from bot.core.set_vars import set_val
import logging
from bot.uploaders.rclone.rclone_copy import RcloneCopy

torlog = logging.getLogger(__name__)


async def handle_setting_copy_menu_callback(callback_query):
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
            msg= f'Select file or folder which you want to copy\n\nPath: `{origin_drive}`', 
            drive_name= cmd[2],
            submenu="list_drive", 
            data_cb="list_dir_origin",
            data_back_cb= "cp_menu_origin",
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
             msg=f"Select file or folder which you want to copy\n\nPath:`{origin_drive}:{rclone_dir}`", 
             drive_base=rclone_dir, 
             drive_name= origin_drive,
             data_cb="list_dir_origin",
             data_back_cb="origin_m_back",
             submenu="list_drive",
             is_second_menu= False
             )

    elif cmd[1] == "rclone_menu_copy":
        #True if click on a File, False if click on Folder
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
                data_cb="list_drive_dest",
                )
        else:
            await settings_copy_menu(
                callback_query,
                mmes, 
                edit=True, 
                msg=f"Select cloud where to copy files", 
                submenu="rclone_menu_copy", 
                data_cb="list_drive_dest",
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
            data_back_cb= "cp_menu_dest",
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
             data_back_cb= "dest_m_back",
             submenu="list_drive", 
             is_second_menu= True
             )        
 
    elif cmd[1] == "start_copy":
        origin_dir = get_val("ORIGIN_DIR")
        origin_dir= origin_dir.split("/")[-2] + "/"
        rclone_dir= get_val("DEST_DIR")
        set_val("DEST_DIR", rclone_dir + origin_dir)
        rclone_copy= RcloneCopy(callback_query)
        GLOBAL_RC_INST.append(rclone_copy)
        await rclone_copy.copy()
        GLOBAL_RC_INST.remove(rclone_copy)

    elif cmd[1] == "selfdest":
        await callback_query.answer("Closed")
        await callback_query.delete()

    #.........BACK BUTTONS HANDLING........#  

    # ORIGIN MENU

    elif cmd[1] == "origin_m_back":
        data_b_cb= "origin_m_back"
        origin_drive = get_val("ORIGIN_DRIVE")
        rclone_dir= get_val("ORIGIN_DIR")
        dir_list= rclone_dir.split("/")
        dir_list = dir_list[: len(dir_list) - 2]
        listToStr = '/'.join([elem for elem in dir_list])
        rclone_dir= listToStr
        set_val("ORIGIN_DIR", rclone_dir)
        
        if rclone_dir == "": data_b_cb= "cp_menu_origin"

        await settings_copy_menu(
             query= callback_query,
             mmes= mmes, 
             edit=True, 
             msg=f"Select file or folder which you want to copy\n\nPath:`{origin_drive}:{rclone_dir}`", 
             drive_base=rclone_dir, 
             drive_name= origin_drive,
             data_cb="list_dir_origin",
             data_back_cb= data_b_cb,
             submenu="list_drive",
             is_second_menu= False
             )   
    
    elif cmd[1]== "cp_menu_origin":
        await settings_copy_menu(
            callback_query, 
            mmes, 
            msg= "Select cloud where your files are stored",
            submenu= "rclone_menu_copy",
            data_cb="list_drive_origin",
            edit=True
        )

    # DESTINATION MENU

    elif cmd[1] == "dest_m_back":
        data_b_cb= "dest_m_back"
        dest_drive = get_val("DEST_DRIVE")
        rclone_dir=  get_val("DEST_DIR")
        dir_list= rclone_dir.split("/")
        dir_list = dir_list[: len(dir_list) - 2]
        listToStr = '/'.join([elem for elem in dir_list])
        rclone_dir= listToStr
        logging.info(rclone_dir)
        set_val("DEST_DIR", rclone_dir)
        
        if rclone_dir == "": data_b_cb= "cp_menu_dest"

        await settings_copy_menu(
             callback_query,
             mmes, 
             edit=True, 
             msg=f"Select folder where you want to copy\n\nPath:`{dest_drive}:{rclone_dir}`", 
             drive_base=rclone_dir, 
             drive_name= dest_drive,
             data_cb="list_dir_dest",
             data_back_cb= data_b_cb,
             submenu="list_drive", 
             is_second_menu= True
             )   

    elif cmd[1]== "cp_menu_dest":
        await settings_copy_menu(
            callback_query, 
            mmes, 
            msg= f"Select cloud where to copy files", 
            submenu= "rclone_menu_copy",
            data_cb="list_drive_dest",
            edit=True
        )          

                

