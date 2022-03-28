from bot.core.get_vars import get_val
from bot.core.menus.menu_copy import settings_copy_menu


async def handle_copy_command(message):
        user_id= message.sender_id
        chat_id= message.chat_id
        if user_id in get_val("ALLOWED_USERS") or chat_id in get_val("ALLOWED_CHATS") or user_id == get_val("OWNER_ID"):
                await settings_copy_menu(
                        message, 
                        msg= "Select cloud where your files are stored", 
                        submenu= "rclone_menu_copy", 
                        data_cb="list_drive_origin"
                )
        else:
                await message.reply('Not Authorized user')      