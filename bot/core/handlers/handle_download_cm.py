from bot.core.set_vars import set_val
from bot.utils.get_message_type import get_message_type
from bot.utils.get_size_p import get_size
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


async def handle_download_command(client, message):
    header_m = "**Which name you want to use?**\n\n"
    replied_message= message.reply_to_message
    if replied_message is not None :
            if replied_message.text is None:

                message_type = get_message_type(replied_message)
                name= message_type.file_name
                size= get_size(message_type.file_size)
                msg= f"Name: `{name}`\n\nSize: `{size}`"
        
                set_val("MESSAGE_TYPE", message_type)
                    
                keyboard = [[InlineKeyboardButton(f"📄 By default", callback_data= f'renaming default'),
                            InlineKeyboardButton(f"📝 Rename", callback_data='renaming rename')],
                            [InlineKeyboardButton("Close", callback_data= f"mainmenu^selfdest")]]

                reply_markup = InlineKeyboardMarkup(keyboard)

                await message.reply(header_m + msg, reply_markup= reply_markup)
            else:
               await message.reply_text("Reply to a Telegram file", quote= True)          
    else:
        await message.reply_text("Reply to a Telegram file", quote= True) 