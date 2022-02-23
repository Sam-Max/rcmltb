
from bot.core.handlers_cb.settings_copy_menu_cb import handle_setting_copy_menu_callback
from bot.utils.admin_check import is_admin


async def handle_copy_command(e):
    if await is_admin(e.sender_id):
            await handle_setting_copy_menu_callback(e, msg= "Seleccione unidad origen", submenu= "rclone_menu_copy", data_cb= "list_drive_origin_cb", is_main_m=False)
    else:
       await e.delete()