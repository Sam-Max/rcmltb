import logging
from bot.core.get_vars import get_val
from bot.core.handlers.settings_main_menu import general_input_manager, get_value, handle_settings_main_menu
from bot.core.set_vars import set_val

torlog = logging.getLogger(__name__)

async def handle_setting_main_menu_callback(callback_query):
    data = callback_query.data.decode()
    cmd = data.split("^")
    mmes = await callback_query.get_message()
    val = ""
    base_dir= get_val("BASE_DIR")
    rclone_drive = get_val("DEF_RCLONE_DRIVE")

    if callback_query.data == "pages":
        await callback_query.answer()

    if cmd[1] == "load_rclone_config":
        await callback_query.answer("Envíe el archivo de configuración rclone.conf", alert=True)
        await mmes.edit(f"Envie el archivo rclone.conf\n\n/ignore para ir atras", buttons=None)
        val = await get_value(callback_query, True)

        await general_input_manager(callback_query, mmes, "RCLONE_CONFIG", "str", val, "rclonemenu")

    elif cmd[1] == "list_drive_main_menu":
        set_val("BASE_DIR", "")
        base_dir = get_val("BASE_DIR")
        set_val("DEF_RCLONE_DRIVE", cmd[2])
        await handle_settings_main_menu(
            callback_query, 
            mmes, 
            edit=True,
            msg=f"Seleccione carpeta para subir\n\nRuta:`{cmd[2]}:{base_dir}`", 
            drive_name= cmd[2], 
            rclone_dir= base_dir, 
            submenu="list_drive", 
            data_cb="list_dir_main_menu", 
            is_main_m=True)     

    elif cmd[1] == "list_dir_main_menu":
        rclone_drive = get_val("DEF_RCLONE_DRIVE")
        rclone_dir= get_val("BASE_DIR")
        dir = cmd[2] +"/"
        rclone_dir += dir
        set_val("BASE_DIR", rclone_dir)
        await handle_settings_main_menu(
            callback_query, mmes, 
            edit=True, 
            msg=f"Seleccione carpeta para subir\n\nRuta:`{rclone_drive}:{rclone_dir}`", 
            drive_base=rclone_dir, 
            drive_name= rclone_drive, 
            rclone_dir= cmd[2], 
            submenu="list_drive", 
            data_cb="list_dir_main_menu", 
            is_main_m=True)

    # close menu
    elif cmd[1] == "selfdest":
        await callback_query.answer("Closed")
        await callback_query.delete()