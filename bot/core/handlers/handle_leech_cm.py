
from bot.core.get_vars import get_val
from bot.core.menus.menu_leech import leech_menu

async def handle_zip_leech_command(client, message):
    await leech(client, message, isZip=True)

async def handle_unzip_leech_command(client, message):
    await leech(client, message, extract=True)

async def handle_leech_command(client, message):
    await leech(client, message)

async def leech(client, message, isZip=False, extract=False):
    user_id= message.from_user.id
    chat_id = message.chat.id
    if user_id in get_val("ALLOWED_USERS") or chat_id in get_val("ALLOWED_CHATS") or user_id == get_val("OWNER_ID"):
        await leech_menu(
                client= client, 
                message= message,
                msg= "Select cloud where your files are stored",
                isZip=isZip, 
                extract=extract, 
                submenu= "list_drive",
                data_cb="list_drive_leech_menu"
            ) 
    else:
        await message.reply('Not Authorized user', quote= True)