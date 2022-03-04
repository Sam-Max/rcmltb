
from bot.core.settings_leech_menu import settings_leech_menu
from bot.utils.admin_check import is_admin


async def handle_leech_command(client, message):
    await settings_leech_menu(
             client= client, 
             message= message,
             msg= "Select cloud where your files are stored", 
             data_cb="list_drive_leech_menu"
        ) 