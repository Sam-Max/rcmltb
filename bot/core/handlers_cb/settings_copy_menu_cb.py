from bot.core.get_vars import get_val
from bot.uploaders.rclone_transfer import rclone_copy_transfer
from bot import SessionVars
import logging

torlog = logging.getLogger(__name__)
# logging.getLogger("telethon").setLevel(logging.DEBUG)

TIMEOUT_SEC = 60

no = "❌"
yes = "✅"
drive_icon= "☁️"
header = ""


async def handle_setting_copy_menu_callback(callback_query):
    conf_path = await get_config()
    data = callback_query.data.decode()
    cmd = data.split("^")
    mmes = await callback_query.get_message()
    val = ""
    base_dir= get_val("BASE_DIR")
    rclone_drive = get_val("DEF_RCLONE_DRIVE")

    if callback_query.data == "pages":
        await callback_query.answer()


    if cmd[1] == "list_drive_origin_cb":
        SessionVars.update_var("ORIGIN_DRIVE", cmd[2])
        await handle_settings(callback_query, mmes, edit=True, msg='Seleccione directorio origen', drive_name= cmd[2],submenu="list_drive", data_cb="", is_main_m=False)

    elif cmd[1] == "list_dir_copy_menu":
        rclone_drive_p = get_val("ORIGIN_DRIVE")
        rclone_dir_p= get_val("BASE_DIR_COPY")
        dir_p = cmd[2] +"/"
        rclone_dir_p += dir_p
        SessionVars.update_var("ORIGIN_DIR", cmd[2])
        #SessionVars.update_var("BASE_DIR_COPY", rclone_dir_p)
        await handle_settings(callback_query, mmes, edit=True, msg=f"Seleccione carpeta para subir\n\nRuta:`{rclone_drive_p}:{rclone_dir_p}`", drive_base=rclone_dir_p, drive_name= rclone_drive_p, rclone_dir= cmd[2], submenu="list_drive", data_cb="list_dir_copy_menu", is_main_m=False)

    elif cmd[1] == "rclone_menu_copy_cb":
        logging.info("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        await handle_settings(callback_query, mmes, edit=True, msg="Seleccione unidad destino", submenu="rclone_menu_copy", data_cb="list_drive_dest_cb", is_main_m=False)                         

  
    elif cmd[1] == "list_drive_dest_cb":
        SessionVars.update_var("DEST_DRIVE", cmd[2])
        await handle_settings(callback_query, mmes, edit=True, msg='Seleccione directorio destino', drive_name= cmd[2],
                              submenu="list_drive", data_cb="", is_main_m=False, is_dest_drive=True)
 
    elif cmd[1] == "start_copy_cb":
        SessionVars.update_var("DEST_DIR", cmd[2])
        await rclone_copy_transfer(callback_query, conf_path)                          

    # close menu
    elif cmd[1] == "selfdest":
        await callback_query.answer("Closed")
        await callback_query.delete()
