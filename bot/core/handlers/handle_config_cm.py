import logging
from bot.core.settings_main_menu import settings_main_menu
from bot.utils.admin_check import is_admin


async def handle_config_command(e):
    if await is_admin(e.sender_id):
        logging.info(e)     
        await settings_main_menu(e)
    else:
        await e.delete()    
