from bot import LOGGER
from bot.core.get_vars import get_val
from bot.core.set_vars import set_val
from bot.downloaders.mirror_download import handle_mirror_download
from bot.utils.bot_utils import get_content_type, is_gdrive_link, is_magnet, is_mega_link, is_url
from re import match as re_match
from bot.utils.direct_link_generator import direct_link_generator
from bot.utils.exceptions import DirectDownloadLinkException
from bot.utils.get_message_type import get_file
from bot.utils.get_size_p import get_readable_size
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


async def handle_mirror_command(client, message):
    await mirror(client, message)

async def handle_zip_mirror_command(client, message):
    await mirror(client, message, isZip=True)

async def handle_unzip_mirror_command(client, message):
    await mirror(client, message, extract=True)

async def mirror(client, message, isZip=False, extract=False):
    user_id= message.from_user.id
    chat_id = message.chat.id
    if user_id in get_val("ALLOWED_USERS") or chat_id in get_val("ALLOWED_CHATS") or user_id == get_val("OWNER_ID"):
        replied_message= message.reply_to_message
        if replied_message is not None :
            mesg = message.text
            pswdMsg = mesg.split(' pswd: ')
            if len(pswdMsg) > 1:
                pswd = pswdMsg[1]
                print("Password: {}".format(pswd))
            else:
                pswd= None  
            file= None  
            media_array = [replied_message.document, replied_message.video, replied_message.audio]
            for i in media_array:
                if i is not None:
                    file = i
                    return file
            tag = f"@{replied_message.from_user.username}"
            if file is None:
                reply_text = str(replied_message.text)
                if is_url(reply_text) or is_magnet(reply_text):
                    link = reply_text.strip()     
                    if not is_mega_link(reply_text) and not is_magnet(reply_text) and not is_gdrive_link(reply_text) \
                        and not reply_text.endswith('.torrent'):
                            content_type = get_content_type(reply_text)
                            if content_type is None or re_match(r'text/html|text/plain', content_type):
                                try:
                                    link = direct_link_generator(reply_text)
                                    LOGGER.info(f"Generated link: {link}")
                                except DirectDownloadLinkException as e:
                                    if str(e).startswith('ERROR:'):
                                        return await message.reply_text(str(e))
                    if is_gdrive_link(reply_text):
                        return await message.reply_text("Bot don't support Google drive links")
                else:
                    return await message.reply_text("<b>Reply to a link or Telegram file</b>", quote=True)    
                await handle_mirror_download(client, message, file, tag, pswd, link, isZip, extract)
            else:
                size= get_readable_size(file.file_size)
                msg = f"<b>Which name do you want to use?</b>\n\n<b>Name</b>: `{file.file_name}`\n\n<b>Size</b>: `{size}`"
                set_val("FILE", file)
                set_val("IS_ZIP", isZip)
                set_val("EXTRACT", extract)
                set_val("PSWD", pswd)
                keyboard = [[InlineKeyboardButton(f"📄 By default", callback_data= f'mirrormenu_default'),
                        InlineKeyboardButton(f"📝 Rename", callback_data='mirrormenu_rename')],
                        [InlineKeyboardButton("Close", callback_data= f"mirrorsetmenu^selfdest")]]
                await message.reply_text(msg, quote= True, reply_markup= InlineKeyboardMarkup(keyboard))
        else:
           if isZip or extract:
                await message.reply_text("<b>Reply to a link or Telegram file</b>\n\n<b>For password use this format:</b>\n/zipmirror pswd: password", quote=True) 
           else:
                await message.reply_text("<b>Reply to a link or Telegram file</b>\n", quote=True) 
    else:
        await message.reply('Not Authorized user', quote= True)


    