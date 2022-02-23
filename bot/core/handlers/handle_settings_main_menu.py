from bot.core.handlers.settings_main_menu import handle_settings_main_menu
from bot.utils.admin_check import is_admin


async def handle_settings_command(e):
    if await is_admin(e.sender_id):
        await handle_settings_main_menu(e)
    else:
        await e.delete()    
