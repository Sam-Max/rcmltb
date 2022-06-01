from bot.core.get_vars import get_val
from bot.core.set_vars import set_val
from bot.utils.bot_utils import is_magnet, is_url
from bot.utils.get_message_type import get_file
from bot.utils.get_size_p import get_size
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

header_m = "**Which name do you want to use?**\n\n"

async def handle_mirror_command(client, message):
    await mirror(client, message)

async def handle_zip_mirror_command(client, message):
    await mirror(client, message, isZip=True)

async def handle_unzip_mirror_command(client, message):
    await mirror(client, message, extract=True)

async def mirror(client, message, isZip=False, extract=False):
    user_id= message.from_user.id
    chat_id = message.chat.id
    mesg = message.text
    pswdMsg = mesg.split(' pswd: ')
    if len(pswdMsg) > 1:
        pswd = pswdMsg[1]
        print("Password: {}".format(pswd))
    else:
        pswd= None  
    if user_id in get_val("ALLOWED_USERS") or chat_id in get_val("ALLOWED_CHATS") or user_id == get_val("OWNER_ID"):
        replied_message= message.reply_to_message
        if replied_message is not None :
                    file = get_file(replied_message)
                    msg= ""
                    link= None
                    if file is None:
                        reply_text = message.reply_to_message.text
                        if is_url(reply_text) or is_magnet(reply_text):
                            link = reply_text.strip()
                    else:
                        name= file.file_name
                        size= get_size(file.file_size)
                        msg= f"**Name**: `{name}`\n\n**Size**: `{size}`"
                    set_val("MEDIA", file)
                    set_val("LINK", link)
                    set_val("IS_ZIP", isZip)
                    set_val("EXTRACT", extract)
                    set_val("PSWD", pswd)
                        
                    keyboard = [[InlineKeyboardButton(f"📄 By default", callback_data= f'mirrormenu_default'),
                                InlineKeyboardButton(f"📝 Rename", callback_data='mirrormenu_rename')],
                                [InlineKeyboardButton("Close", callback_data= f"mirrorsetmenu^selfdest")]]

                    await message.reply_text(header_m + msg, quote= True, reply_markup= InlineKeyboardMarkup(keyboard))
        else:
            await message.reply_text("Reply to a link or telegram file", quote=True) 
    else:
        await message.reply('Not Authorized user', quote= True)