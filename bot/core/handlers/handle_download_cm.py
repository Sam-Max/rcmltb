from bot.core.set_vars import set_val
from bot.utils.get_message_type import get_media_type
from bot.utils.get_size_p import get_size
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


async def handle_download_command(client, message):
    header_m = "**Which name do you want to use?**\n\n"
    replied_message= message.reply_to_message
    if replied_message is not None :
                media = get_media_type(replied_message)
                name= media.file_name
                size= get_size(media.file_size)
                msg= f"**Name**: `{name}`\n\n**Size**: `{size}`"
                set_val("MEDIA", media)
                    
                keyboard = [[InlineKeyboardButton(f"📄 By default", callback_data= f'renaming default'),
                            InlineKeyboardButton(f"📝 Rename", callback_data='renaming rename')],
                            [InlineKeyboardButton("Close", callback_data= f"mainmenu^selfdest")]]

                await message.reply_text(header_m + msg, quote= True, reply_markup= InlineKeyboardMarkup(keyboard))
    else:
        await message.reply_text("Reply to a telegram file", quote= True) 