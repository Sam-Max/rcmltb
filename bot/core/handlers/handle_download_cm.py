from bot.core.set_vars import set_val
from bot.utils.get_file_id import get_message_type
from bot.utils.get_size_p import get_size
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

default= "📄"
rename= "📝"

async def handle_download_command(client, message):
    header_m = "Que nombre quieres usar?\n\n"
    replied_message= message.reply_to_message
    if replied_message is not None :
            if replied_message.text is None:

                message_type = get_message_type(replied_message)
                name= message_type.file_name
                size= get_size(message_type.file_size)
                msg= f"Nombre: `{name}`\n\nTamaño: `{size}`"
        
                set_val("MESSAGE_TYPE", message_type)
                    
                keyboard = [[InlineKeyboardButton(f"{default} Por Defecto", callback_data= f'renaming default'),
                            InlineKeyboardButton(f"{rename} Renombrar", callback_data='renaming rename')],
                            [InlineKeyboardButton("Cerrar", callback_data= f"mainmenu^selfdest")]]

                reply_markup = InlineKeyboardMarkup(keyboard)

                await message.reply_text(header_m + msg, reply_markup= reply_markup)
            else:
               await message.reply("Responda a un archivo, por favor")          
    else:
        await message.reply("Responda a un archivo de Telegram para subir a la nube") 