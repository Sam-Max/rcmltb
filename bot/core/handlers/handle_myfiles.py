from bot import ALLOWED_CHATS, ALLOWED_USERS, OWNER_ID
from bot.core.menus.menu_myfiles import myfiles_menu


async def handle_myfiles(client, message):
    user_id= message.from_user.id
    chat_id = message.chat.id
    if user_id in ALLOWED_USERS or chat_id in ALLOWED_CHATS or user_id == OWNER_ID:
         await myfiles_menu(
                client, 
                message,
                msg= "Please select your drive to see files", 
                submenu="list_drive",
                data_cb="list_drive_myfiles_menu")
    else:
        await message.reply('Not Authorized user', quote=True)