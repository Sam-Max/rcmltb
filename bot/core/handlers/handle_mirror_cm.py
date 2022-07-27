import os
from time import time
from requests import get
from bot import LOGGER, MEGA_KEY
from bot.core.get_vars import get_val
from bot.core.set_vars import set_val
from bot.downloaders.aria.aria_download import AriaDownloader
from bot.downloaders.mega.mega_download import MegaDownloader
from bot.downloaders.qbit.qbit_downloader import QbDownloader
from bot.uploaders.rclone.rclone_mirror import RcloneMirror
from bot.utils.bot_utils.bot_utils import get_content_type, is_gdrive_link, is_magnet, is_mega_link, is_url
from re import match as re_match
from bot.utils.bot_utils.direct_link_generator import direct_link_generator
from bot.utils.bot_utils.exceptions import DirectDownloadLinkException
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils.bot_utils.misc_utils import clean_path, get_rclone_config, get_readable_size


async def handle_mirror_command(client, message):
    await mirror(client, message)

async def handle_zip_mirror_command(client, message):
    await mirror(client, message, isZip=True)

async def handle_unzip_mirror_command(client, message):
    await mirror(client, message, extract=True)

async def handle_qbit_mirror_command(client, message):
    await mirror(client, message, isQbit=True)

async def mirror(client, message, isZip=False, extract=False, isQbit=False):
    user_id= message.from_user.id
    chat_id = message.chat.id
    if user_id in get_val("ALLOWED_USERS") or chat_id in get_val("ALLOWED_CHATS") or user_id == get_val("OWNER_ID"):
        if await get_rclone_config() is None:
            return await message.reply_text("Rclone config file not found.")
        if len(get_val("DEFAULT_RCLONE_DRIVE")) == 0:
            return await message.reply_text("You need to select a cloud first, use /mirrorset")
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
            tag = f"@{replied_message.from_user.username}"
            if file is not None:
                if isQbit: 
                    try:
                        path = await client.download_media(file)
                        file_name = str(time()).replace(".", "") + ".torrent"
                        with open(path, "rb") as f:
                            with open(file_name, "wb") as t:
                                t.write(f.read())
                        link = str(file_name)
                    except Exception as error:
                        return await message.reply_text(tag + " " + error)    
                    mess_age= await message.reply_text('Qbit download started...')
                    qbit_dl= QbDownloader(mess_age)
                    state, message, path, name= await qbit_dl.add_qb_torrent(link)
                    if not state:
                        await mess_age.edit(message)
                        clean_path(path)
                    else:
                        await RcloneMirror(path, mess_age, tag, torrent_name= name).mirror()
                if file.mime_type != "application/x-bittorrent":
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
                else:
                    return await message.reply_text("Use qbmirror command to mirror torrent file")   
            else:
                reply_text = replied_message.text     
                link = reply_text.strip()
                if isQbit and not is_magnet(reply_text):
                    if link.endswith('.torrent'):
                        content_type = None
                    else:
                        content_type = get_content_type(link)
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
                                return await message.reply_text(tag + " " + error.split("'")[1])
                            else:
                                return await message.reply_text(tag + " " + error)
                if isQbit and (is_magnet(link) or os.path.exists(link)):
                    mess_age= await message.reply_text('Qbit download started...')
                    qbit_dl= QbDownloader(mess_age)
                    state, message, path, name = await qbit_dl.add_qb_torrent(link)
                    if not state:
                        await mess_age.edit(message)
                        clean_path(path)
                    else:
                        await RcloneMirror(path, mess_age, tag, torrent_name= name).mirror()
                
                if is_magnet(link) or link.endswith('.torrent'):
                    return await message.reply_text("Use qbmirror command to mirror torrent or magnet link")
                elif is_gdrive_link(link):
                    return await message.reply_text("Not currently supported Google Drive links") 
                elif is_mega_link(link):
                    if MEGA_KEY is not None:
                        mess_age= await message.reply_text('Mega download started...')     
                        mega_dl= MegaDownloader(link, mess_age)   
                        state, message, path= await mega_dl.execute()
                        if not state:
                            await mess_age.edit(message)
                            clean_path(path)
                        else:
                            await RcloneMirror(path, mess_age, tag).mirror()
                    else:
                        await mess_age.edit("MEGA_API_KEY not provided!")
                elif not is_mega_link(link) and not is_magnet(link) and not is_gdrive_link(link) \
                    and not link.endswith('.torrent'):
                    content_type = get_content_type(link)
                    if content_type is None or re_match(r'text/html|text/plain', content_type):
                        try:
                            link = direct_link_generator(link)
                            LOGGER.info(f"Generated link: {link}")
                        except DirectDownloadLinkException as e:
                            if str(e).startswith('ERROR:'):
                                return await message.reply_text(str(e))
                    mess_age= await message.reply_text('Starting Download...')     
                    aria2= AriaDownloader(link, mess_age)   
                    state, message, path= await aria2.execute()
                    if not state:
                        await mess_age.edit(message)
                    else:
                        await RcloneMirror(path, mess_age, tag).mirror()  
        else:
            if isZip or extract:
                await message.reply_text("<b>Reply to a Telegram file</b>\n\n<b>For password use this format:</b>\n/zipmirror pswd: password", quote=True) 
            elif isQbit:
                await message.reply_text("<b>Reply to a torrent or magnet link</b>", quote=True)
            else:
                await message.reply_text("<b>Reply to a link or Telegram file</b>\n", quote=True) 
    else:
        await message.reply('Not Authorized user', quote=True)


    