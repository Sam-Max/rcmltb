
from bot import ALLOWED_CHATS, ALLOWED_USERS, OWNER_ID
from bot.core.menus.menu_leech import leech_menu
from bot.core.varholderwrap import set_val

async def handle_zip_leech_command(client, message):
    await leech(client, message, isZip=True)

async def handle_unzip_leech_command(client, message):
    await leech(client, message, extract=True)

async def handle_leech_command(client, message):
    await leech(client, message)

async def leech(client, message, isZip=False, extract=False):
    user_id= message.from_user.id
    chat_id = message.chat.id
    if user_id in ALLOWED_USERS or chat_id in ALLOWED_CHATS or user_id == OWNER_ID:
        set_val('IS_ZIP', isZip)   
        set_val('EXTRACT', extract)    
        await leech_menu(
                client, 
                message,
                msg= "Select cloud where your files are stored",
                submenu= "list_drive",
                data_cb="list_drive_leech_menu"
            ) 
    else:
        await message.reply('Not Authorized user', quote= True)