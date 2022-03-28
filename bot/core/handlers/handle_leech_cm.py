
from bot.core.get_vars import get_val
from bot.core.menus.menu_leech import settings_leech_menu


async def handle_leech_command(client, message):
    user_id= message.from_user.id
    chat_id = message.chat.id
    if user_id in get_val("ALLOWED_USERS") or chat_id in get_val("ALLOWED_CHATS") or user_id == get_val("OWNER_ID"):
        await settings_leech_menu(
                client= client, 
                message= message,
                msg= "Select cloud where your files are stored", 
                data_cb="list_drive_leech_menu"
            ) 
    else:
        await message.reply('Not Authorized user', quote= True)