import time
from requests import get
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

async def handle_qbit_mirror_command(client, message):
    await mirror(client, message, extract=True, isQbit=True)

async def mirror(client, message, isZip=False, extract=False, isQbit=False):
    user_id= message.from_user.id
    chat_id = message.chat.id
    if user_id in get_val("ALLOWED_USERS") or chat_id in get_val("ALLOWED_CHATS") or user_id == get_val("OWNER_ID"):
        replied_message= message.reply_to_message
        qbitsel = False
        if replied_message is not None :
            mesg = message.text
            pswdMsg = mesg.split(' pswd: ')
            if len(pswdMsg) > 1:
                pswd = pswdMsg[1]
                print("Password: {}".format(pswd))
            else:
                pswd= None  
            file = get_file(replied_message)
            tag = f"@{replied_message.from_user.username}"
            reply_text = str(replied_message.text)
            if not is_url(reply_text) and not is_magnet(reply_text) or len(reply_text) == 0:
                if file is None:
                    return await message.reply_text("<b>Reply to a link or Telegram file</b>", quote=True)    
                if file.mime_type != "application/x-bittorrent" and not isQbit:
                    name= file.file_name
                    size= get_readable_size(file.file_size)
                    msg = f"<b>Which name do you want to use?</b>\n\n<b>Name</b>: `{name}`\n\n<b>Size</b>: `{size}`"
                    set_val("FILE", file)
                    set_val("IS_ZIP", isZip)
                    set_val("EXTRACT", extract)
                    set_val("PSWD", pswd)
                    keyboard = [[InlineKeyboardButton(f"📄 By default", callback_data= f'mirrormenu_default'),
                            InlineKeyboardButton(f"📝 Rename", callback_data='mirrormenu_rename')],
                            [InlineKeyboardButton("Close", callback_data= f"mirrorsetmenu^selfdest")]]
                    return await message.reply_text(msg, quote= True, reply_markup= InlineKeyboardMarkup(keyboard))
                if isQbit:
                    if reply_text.endswith('.torrent') or "https://api.telegram.org/file/" in reply_text:
                        content_type = None
                    else:
                        content_type = get_content_type(reply_text)
                    if content_type is None or re_match(r'application/x-bittorrent|application/octet-stream', content_type):
                        try:
                            resp = get(link, timeout=10, headers = {'user-agent': 'Wget/1.12'})
                            if resp.status_code == 200:
                                file_name = str(time()).replace(".", "") + ".torrent"
                                with open(file_name, "wb") as t:
                                    t.write(resp.content)
                                link = str(file_name)
                            else:
                                return await message.reply_text(f"{tag} ERROR: link got HTTP response: {resp.status_code}")     
                        except Exception as e:
                            error = str(e).replace('<', ' ').replace('>', ' ')
                            if error.startswith('No connection adapters were found for'):
                                link = error.split("'")[1]
                            else:
                                LOGGER.error(str(e))
                                return await message.reply_text(tag + " " + error)  
                else:
                    return await message.reply_text("Can't download .torrent file", quote=True)    
                await handle_mirror_download(client, message, file, tag, pswd, link, isZip, extract, isQbit, qbitsel)
            
            if is_url(reply_text) or is_magnet(reply_text):
                link = reply_text.strip()
                # if reply_text.startswith("s ") or reply_text == "s":
                #      qbitsel = True
                #      link = reply_text.strip()
                if not is_mega_link(reply_text) and not isQbit and not is_magnet(reply_text) and not is_gdrive_link(reply_text) \
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
                    return await message.reply_text("Not supported Google drive links")
            await handle_mirror_download(client, message, file, tag, pswd, link, isZip, extract, isQbit, qbitsel)
        else:
           if isZip or extract:
                await message.reply_text("<b>Reply to a link or Telegram file</b>\n\n<b>For password use this format:</b>\n/zipmirror pswd: password", quote=True) 
           else:
                await message.reply_text("<b>Reply to a link or Telegram file</b>\n", quote=True) 
    else:
        await message.reply('Not Authorized user', quote= True)


    