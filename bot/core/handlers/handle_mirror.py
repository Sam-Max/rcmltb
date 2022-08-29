from os import listdir, path as ospath
from time import time
from requests import get
from bot import ALLOWED_CHATS, ALLOWED_USERS, DOWNLOAD_DIR, LOGGER, MEGA_KEY, OWNER_ID
from bot.core.varholderwrap import get_val, set_val
from bot.downloaders.aria.aria2_download import Aria2Downloader
from bot.downloaders.mega.mega_download import MegaDownloader
from bot.downloaders.qbit.qbit_downloader import QbDownloader
from bot.uploaders.rclone.rclone_clone import GDriveClone
from bot.uploaders.rclone.rclone_mirror import RcloneMirror
from bot.utils.bot_utils.bot_utils import get_content_type, is_gdrive_link, is_magnet, is_mega_link, is_url
from re import match as re_match
from bot.utils.bot_utils.direct_link_generator import direct_link_generator
from bot.utils.bot_utils.exceptions import DirectDownloadLinkException
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils.bot_utils.message_utils import sendMarkup, sendMessage
from bot.utils.bot_utils.misc_utils import get_readable_size


async def handle_mirror_command(client, message):
    await mirror(client, message)

async def handle_zip_mirror_command(client, message):
    await mirror(client, message, isZip=True)

async def handle_unzip_mirror_command(client, message):
    await mirror(client, message, extract=True)

async def handle_qbit_mirror_command(client, message):
    await mirror(client, message, isQbit=True)

async def handle_clone_command(client, message):
    await mirror(client, message, isGclone= True)

async def mirror(client, message, isZip=False, extract=False, isQbit=False, isGclone= False):
    user_id= message.from_user.id
    chat_id = message.chat.id
    reply_message= message.reply_to_message
    select = False
    if user_id in ALLOWED_USERS or chat_id in ALLOWED_CHATS or user_id == OWNER_ID:
        msg = message.text
        args = msg.split(maxsplit=1)
        if len(args) > 1:
            arg = args[1]
            if arg == 's':
                select = True 
        pswdMsg = msg.split(' pswd: ', maxsplit=1)
        if len(pswdMsg) > 1:
            pswd = pswdMsg[1]
        else:
            pswd= None  
        file= None
        if reply_message is not None:
            if len(get_val("RCLONE_MIRRORSET_DRIVE")) == 0:
                 return await sendMessage("You need to select a cloud first, use /mirrorset", message)
            file = reply_message.document or reply_message.video or reply_message.audio or reply_message.photo or None
            if reply_message.from_user.username:
                 tag = f"@{reply_message.from_user.username}"
            if file is None:
                reply_text= reply_message.text.strip()      
                if is_url(reply_text) or is_magnet(reply_text):     
                     link = reply_text
                else:
                    return        
            elif file.mime_type != "application/x-bittorrent":
                    name= file.file_name
                    size= get_readable_size(file.file_size)
                    header_msg = f"<b>Which name do you want to use?</b>\n\n<b>Name</b>: `{name}`\n\n<b>Size</b>: `{size}`"
                    set_val("FILE", file)
                    set_val("IS_ZIP", isZip)
                    set_val("EXTRACT", extract)
                    set_val("PSWD", pswd)
                    keyboard = [[InlineKeyboardButton(f"📄 By default", callback_data= f'mirrormenu_default'),
                            InlineKeyboardButton(f"📝 Rename", callback_data='mirrormenu_rename')],
                            [InlineKeyboardButton("Close", callback_data= f"mirrorsetmenu^close")]]
                    return await sendMarkup(header_msg, message, reply_markup= InlineKeyboardMarkup(keyboard))
            else:
                try:
                    path = await client.download_media(file)
                    file_name = str(time()).replace(".", "") + ".torrent"
                    with open(path, "rb") as f:
                        with open(file_name, "wb") as t:
                            t.write(f.read())
                    link = str(file_name)
                except Exception as ex:
                    return await sendMessage(tag + " " + str(ex), message) 
            if not is_mega_link(link) and not is_magnet(link) and not is_gdrive_link(link) \
                and not link.endswith('.torrent'):
                content_type = get_content_type(link)
                if content_type is None or re_match(r'text/html|text/plain', content_type):
                    try:
                        link = direct_link_generator(link)
                        LOGGER.info(f"Generated link: {link}")
                    except DirectDownloadLinkException as e:
                        if str(e).startswith('ERROR:'):
                            return await sendMessage(str(e), message)
            elif not is_magnet(link) and not ospath.exists(link):
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
                            return await sendMessage(f"{tag} ERROR: link got HTTP response: {resp.status_code}", message)     
                    except Exception as e:
                        error = str(e).replace('<', ' ').replace('>', ' ')
                        if error.startswith('No connection adapters were found for'):
                            return await sendMessage(tag + " " + error.split("'")[1], message)
                        else:
                            return await sendMessage(tag + " " + error, message)
            if is_mega_link(link):
                if MEGA_KEY is not None:
                    mega_dl= MegaDownloader(link, message)   
                    state, rmsg, path= await mega_dl.execute(path= f'{DOWNLOAD_DIR}{message.id}')
                    if state:
                        rclone_mirror = RcloneMirror(path, rmsg, tag)
                        await rclone_mirror.mirror()
                else:
                    await sendMessage("MEGA_API_KEY not provided!", message)
            elif isGclone:
                    gd_clone = GDriveClone(message, link)
                    await gd_clone.execute()
            elif is_magnet(link) or ospath.exists(link):
                qbit_dl= QbDownloader(message)
                path = f'{DOWNLOAD_DIR}{message.id}'
                state, rmsg, name = await qbit_dl.add_qb_torrent(link, path, select)
                if state:
                    if name == "None" or not ospath.exists(f'{path}/{name}'):
                        name = listdir(path)[-1]
                        path = f'{path}/{name}'
                    else:
                        path= f'{path}/{name}'     
                    rclone_mirror = RcloneMirror(path, rmsg, tag)
                    await rclone_mirror.mirror()
            else:
                aria2= Aria2Downloader(link, message)   
                path = f'{DOWNLOAD_DIR}{message.id}'
                state, rmsg, name= await aria2.execute(path)
                if state:
                    if not ospath.exists(f'{path}/{name}'):
                        name = listdir(path)[-1]
                        path = f'{path}/{name}'
                    else:
                        path= f'{path}/{name}'      
                    rclone_mirror= RcloneMirror(path, rmsg, tag)
                    await rclone_mirror.mirror() 
        else:
            if isZip or extract:
                help_msg =  "<b>Reply to file</b>\n\n"   
                help_msg +=  "<b>For password use this format:</b>\n"
                help_msg +=  "<code>/zipmirror</code> pswd: pass"   
                await sendMessage(help_msg, message) 
            elif isQbit:
                help_msg = "<b>Reply to a torrent or magnet link</b>\n\n"
                help_msg += "<b>Bittorrent selection:</b>\n"     
                help_msg += "<code>/qbitmirror</code> <b>s</b>"
                await sendMessage(help_msg, message)
            elif isGclone:
                help_msg = "<b>Reply to a Google Drive link</b>\n\n"
                help_msg += "<b>Format for Folder:</b> gdrive link | folder name\n"
                help_msg += "<b>Format for File:</b> gdrive link"
                await sendMessage(help_msg, message)
            else:
                await sendMessage("<b>Reply to a link/torrent/file</b>\n", message) 
    else:
        await sendMessage('Not Authorized user', message)


    