from bot import ALLOWED_CHATS, ALLOWED_USERS, OWNER_ID
from bot.core.menus.menu_mirrorset import mirrorset_menu
from bot.core.varholderwrap import get_val


async def handle_mirrorset_command(message):
    user_id= message.sender_id
    chat_id= message.chat_id
    if user_id in ALLOWED_USERS or chat_id in ALLOWED_CHATS or user_id == OWNER_ID:
        base_dir= get_val("MIRRORSET_BASE_DIR")
        rclone_drive = get_val("RCLONE_MIRRORSET_DRIVE")     
        await mirrorset_menu(
            query="",
            message= message,
            submenu= "list_drive",
            msg= f"Select cloud where you want to upload file\n\nPath:`{rclone_drive}:{base_dir}`"
            )
    else:
        await message.reply('Not Authorized user') 
