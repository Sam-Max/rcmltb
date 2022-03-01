from bot.core.handlers.settings_copy_menu import handle_settings_copy_menu
from bot.utils.admin_check import is_admin


async def handle_copy_command(e):
    if await is_admin(e.sender_id):
            await handle_settings_copy_menu(e, msg= "Select cloud where your files are stored", submenu= "rclone_menu_copy", data_cb="list_drive_origin")
    else:
       await e.delete()