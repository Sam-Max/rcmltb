from bot.core.get_vars import get_val
from bot.core.set_vars import set_val
from bot.utils.get_message_type import get_media_type
from bot.utils.get_size_p import get_size
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

header_m = "**Which name do you want to use?**\n\n"

async def handle_mirror_command(client, message):
    await mirror(client, message)

async def handle_unzip_mirror_command(client, message):
    await mirror(client, message, isZip=True)

async def mirror(client, message, isZip=False):
    user_id= message.from_user.id
    chat_id = message.chat.id
    if user_id in get_val("ALLOWED_USERS") or chat_id in get_val("ALLOWED_CHATS") or user_id == get_val("OWNER_ID"):
        replied_message= message.reply_to_message
        if replied_message is not None :
                    media = get_media_type(replied_message)
                    name= media.file_name
                    size= get_size(media.file_size)
                    msg= f"**Name**: `{name}`\n\n**Size**: `{size}`"
                    set_val("MEDIA", media)
                    set_val("IS_ZIP", isZip)
                        
                    keyboard = [[InlineKeyboardButton(f"📄 By default", callback_data= f'mirrormenu_default'),
                                InlineKeyboardButton(f"📝 Rename", callback_data='mirrormenu_rename')],
                                [InlineKeyboardButton("Close", callback_data= f"mirrorsetmenu^selfdest")]]

                    await message.reply_text(header_m + msg, quote= True, reply_markup= InlineKeyboardMarkup(keyboard))
        else:
            await message.reply_text("Reply to a telegram file", quote= True) 
    else:
        await message.reply('Not Authorized user', quote= True)