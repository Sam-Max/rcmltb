from bot.core.get_vars import get_val
from bot.core.menus.menu_myfiles import myfiles_menu


async def handle_myfiles(client, message):
    user_id= message.from_user.id
    chat_id = message.chat.id
    if user_id in get_val("ALLOWED_USERS") or chat_id in get_val("ALLOWED_CHATS") or user_id == get_val("OWNER_ID"):
         await myfiles_menu(
                client= client, 
                message= message,
                msg= "Please select your drive to see files", 
                data_cb="list_drive_myfiles_menu"
            )
    else:
        await message.reply('Not Authorized user', quote=True)