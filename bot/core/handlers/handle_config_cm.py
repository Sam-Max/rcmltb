from bot.core.get_vars import get_val
from bot.core.menus.main_menu import settings_main_menu


async def handle_config_command(message):
    user_id= message.sender_id
    chat_id= message.chat_id
    if user_id in get_val("ALLOWED_USERS") or chat_id in get_val("ALLOWED_CHATS") or user_id == get_val("OWNER_ID"):
        await settings_main_menu(message)
    else:
        await message.reply('Not Authorized user') 
