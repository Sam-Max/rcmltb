from bot import ALLOWED_CHATS, ALLOWED_USERS, OWNER_ID
from bot.core.menus.menu_copy import copy_menu


async def handle_copy_command(message):
        user_id= message.sender_id
        chat_id= message.chat_id
        if user_id in ALLOWED_USERS or chat_id in ALLOWED_CHATS or user_id == OWNER_ID:
                await copy_menu(
                        message, 
                        msg= "Select cloud where your files are stored", 
                        submenu= "list_drive",
                        data_cb= "list_drive_origin"
                )
        else:
                await message.reply('Not Authorized user')      