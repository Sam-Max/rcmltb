from bot.core.get_vars import get_val
from bot.core.handlers.settings_copy_menu import handle_settings_copy_menu
from bot.core.set_vars import set_val
from bot.uploaders.rclone_transfer import rclone_copy_transfer
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

    if cmd[1] == "list_drive_origin":
        set_val("ORIGIN_DRIVE", cmd[2])
        await handle_settings_copy_menu(
            callback_query, 
            mmes, 
            edit=True,
            msg='Seleccione directorio origen', 
            drive_name= cmd[2],submenu="list_drive", 
            is_dest_drive=False
           )

    elif cmd[1] == "list_dir_copy_menu":
        rclone_drive_p = get_val("ORIGIN_DRIVE")
        rclone_dir_p= get_val("BASE_DIR_COPY")
        dir_p = cmd[2] +"/"
        rclone_dir_p += dir_p
        set_val("ORIGIN_DIR", cmd[2])
        #SessionVars.update_var("BASE_DIR_COPY", rclone_dir_p)
        await handle_settings_copy_menu(
             callback_query,
             mmes, 
             edit=True, 
             msg=f"Seleccione carpeta para subir\n\nRuta:`{rclone_drive_p}:{rclone_dir_p}`", 
             drive_base=rclone_dir_p, 
             drive_name= rclone_drive_p,
             rclone_dir= cmd[2], 
             submenu="list_drive", 
             data_cb="list_dir_copy_menu"
             )

    elif cmd[1] == "rclone_menu_copy":
        await handle_settings_copy_menu(
             callback_query,
             mmes, 
             edit=True, 
             msg="Seleccione unidad destino", 
             submenu="rclone_menu_copy", 
             data_cb="list_drive_dest"
             )                         

  
    elif cmd[1] == "list_drive_dest":
        set_val("DEST_DRIVE", cmd[2])
        await handle_settings_copy_menu(
            callback_query, 
            mmes, edit=True, 
            msg='Seleccione directorio destino', 
            drive_name= cmd[2],
            submenu="list_drive", 
            data_cb="", 
            is_second_menu=True)
 
    elif cmd[1] == "start_copy":
        set_val("DEST_DIR", cmd[2])
        await rclone_copy_transfer(callback_query, conf_path)                          

    # close menu
    elif cmd[1] == "selfdest":
        await callback_query.answer("Closed")
        await callback_query.delete()
