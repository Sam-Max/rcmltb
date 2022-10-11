from os import path as ospath
from random import seed
from time import time
from requests import get
from bot import AUTO_MIRROR, DOWNLOAD_DIR, MEGA_KEY, Bot
from asyncio import TimeoutError
from bot import Bot, DOWNLOAD_DIR
from pyrogram import filters
from pyrogram.handlers import CallbackQueryHandler
from pyrogram.types import InlineKeyboardMarkup
from re import match as re_match
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram import filters
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.bot_utils import get_content_type, is_gdrive_link, is_magnet, is_mega_link, is_url
from bot.helper.ext_utils.direct_link_generator import direct_link_generator
from bot.helper.ext_utils.exceptions import DirectDownloadLinkException
from bot.helper.ext_utils.filters import CustomFilters
from bot.helper.ext_utils.message_utils import deleteMessage, sendMarkup, sendMessage
from bot.helper.ext_utils.misc_utils import ButtonMaker, get_readable_size
from bot.helper.ext_utils.rclone_utils import is_rclone_config, is_rclone_drive
from bot.helper.mirror_leech_utils.download_utils.aria2_download import add_aria2c_download
from bot.helper.mirror_leech_utils.download_utils.mega_download import MegaDownloader
from bot.helper.mirror_leech_utils.download_utils.qbit_downloader import add_qb_torrent
from bot.helper.mirror_leech_utils.download_utils.telegram_downloader import TelegramDownloader
from bot.helper.mirror_leech_utils.listener import MirrorLeechListener


listener_dict = {}

async def handle_mirror(client, message):
    await mirror_leech(client, message)

async def handle_zip_mirror(client, message):
    await mirror_leech(client, message, isZip=True)

async def handle_unzip_mirror(client, message):
    await mirror_leech(client, message, extract=True)

async def mirror_leech(client, message, _link= None, isZip=False, extract=False, isLeech= False):
        user_id= message.from_user.id
        message_id= message.id
        if await is_rclone_config(user_id, message) == False:
            return
        if not isLeech:
            if await is_rclone_drive(user_id, message) == False:
                return
        select = False
        pswd= None  
        link= ''
        tag = ''
        msg = message.text.split(maxsplit=1)
        if len(msg) > 1:
            msg_args = msg[1].split(maxsplit=1)
            for x in msg_args:
                x = x.strip()
                if x == 's':
                    select = True
                if is_url(x) or is_magnet(x):
                   link= x         
            pswdMsg = msg[1].split(' pswd: ', maxsplit=1)
            if len(pswdMsg) > 1:
                pswd = pswdMsg[1]

        if message.from_user.username:
            tag = f"@{message.from_user.username}"

        reply_message= message.reply_to_message
        if reply_message is not None:
            file = reply_message.document or reply_message.video or reply_message.audio or reply_message.photo or None
            if reply_message.from_user.username:
                tag = f"@{reply_message.from_user.username}"
            if file is None:
                reply_text= reply_message.text     
                if is_url(reply_text) or is_magnet(reply_text):     
                     link = reply_text.strip() 
            elif file.mime_type != "application/x-bittorrent":
                    buttons= ButtonMaker() 
                    name= file.file_name
                    size= get_readable_size(file.file_size)
                    header_msg = f"<b>Which name do you want to use?</b>\n\n<b>Name</b>: `{name}`\n\n<b>Size</b>: `{size}`"
                    listener= MirrorLeechListener(message, tag, user_id, isZip=isZip, extract=extract, pswd=pswd, isLeech=isLeech)
                    buttons.dbuildbutton("📄 By default", f'mirrormenu^default^{message_id}',
                                         "📝 Rename", f'mirrormenu^rename^{message_id}')
                    buttons.cbl_buildbutton("✘ Close Menu", f"mirrormenu^close^{message_id}")
                    menu_msg= await sendMarkup(header_msg, message, reply_markup= InlineKeyboardMarkup(buttons.first_button))
                    listener_dict[message_id] = [listener, file, menu_msg, user_id]
                    return
            else:
                link = await client.download_media(file)
        
        if _link is not None:
            msgArgs = _link.split(maxsplit=1)
            for x in msgArgs:
                x = x.strip()
                if x == 's':
                   select = True
                if is_url(x) or is_magnet(x):
                   link= x    

        if not is_url(link) and not is_magnet(link):
            if isLeech:
                help_msg = '''         
<code>/cmd</code> along with link pswd: xx(zip/unzip)

<b>qBittorrent Selection</b>    
<b>s</b> along with link 
'''
            else:
                help_msg = '''         
<code>/cmd</code> along with link

<b>By replying</b>   
<code>/cmd</code> link/file pswd: xx(zip/unzip)

<b>qBittorrent Selection</b>    
<code>/cmd</code> <b>s</b> link or by replying to link
'''
            return await sendMessage(help_msg, message)

        listener= MirrorLeechListener(message, tag, user_id, isZip=isZip, extract=extract, pswd=pswd, select=select, isLeech=isLeech)

        if not is_mega_link(link) and not is_magnet(link) and not is_gdrive_link(link) \
            and not link.endswith('.torrent'):
            content_type = get_content_type(link)
            if content_type is None or re_match(r'text/html|text/plain', content_type):
                try:
                    link = direct_link_generator(link)
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
        if is_gdrive_link(link):
            gmsg = f"Use /{BotCommands.CloneCommand} to clone Google Drive file/folder\n\n"
            await sendMessage(gmsg, message)      
        elif is_mega_link(link):
            if MEGA_KEY is not None:
                await MegaDownloader(link, listener).execute(path= f'{DOWNLOAD_DIR}{listener.uid}')   
            else:
                await sendMessage("MEGA_API_KEY not provided!", message)
        elif is_magnet(link) or ospath.exists(link):
            await add_qb_torrent(link, f'{DOWNLOAD_DIR}{listener.uid}', listener)
        else:
            await add_aria2c_download(link, f'{DOWNLOAD_DIR}{listener.uid}', listener, "") 

async def mirror_menu(client, query):
    cmd = query.data.split("^")
    message= query.message
    user_id= query.from_user.id
    msg_id= int(cmd[-1])
    info= listener_dict[msg_id] 
    listener= info[0]
    file = info[1]

    if int(info[-1]) != user_id:
        return await query.answer("This menu is not for you!", show_alert=True)

    elif cmd[1] == "default" :
       await deleteMessage(info[2]) 
       tg_down= TelegramDownloader(file, client, listener, f'{DOWNLOAD_DIR}{listener.uid}/')
       await tg_down.download() 

    elif cmd[1] == "rename": 
        question= await client.send_message(message.chat.id, text= "Send the new name, /ignore to cancel")
        try:
            response = await client.listen.Message(filters.text, id=filters.user(user_id), timeout = 30)
        except TimeoutError:
            await sendMessage("Too late 30s gone, try again!", message)
        else:
            if response:
                if "/ignore" in response.text:
                    await question.reply("Okay cancelled!")
                    await client.listen.Cancel(filters.user(user_id))
                else:
                    listener.newName= response.text
                    listener.isRename= True
                    await deleteMessage(info[2]) 
                    tg_down= TelegramDownloader(file, client, listener, f'{DOWNLOAD_DIR}{listener.uid}/')
                    await tg_down.download() 
        finally:
            await question.delete()

    elif cmd[1] == "close":
        await query.answer("Closed")
        await message.delete()

    del listener_dict[msg_id]

async def handle_auto_mirror(client, message):
    user_id= message.from_user.id
    if await is_rclone_config(user_id, message) == False:
        return
    if await is_rclone_drive(user_id, message) == False:
        return
    file = message.document or message.video or message.audio or message.photo or None
    tag = f"@{message.from_user.username}"
    if file is not None:
        if file.mime_type != "application/x-bittorrent":
            listener= MirrorLeechListener(message, tag, user_id)
            tg_down= TelegramDownloader(file, client, listener, f'{DOWNLOAD_DIR}{listener.uid}/')
            await tg_down.download()  

mirror_handler = MessageHandler(handle_mirror,filters=filters.command(BotCommands.MirrorCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter))
zip_mirror_handler = MessageHandler(handle_zip_mirror,filters=filters.command(BotCommands.ZipMirrorCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter))
unzip_mirror_handler = MessageHandler(handle_unzip_mirror,filters=filters.command(BotCommands.UnzipMirrorCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter))
auto_mirror_handler = MessageHandler(handle_auto_mirror, filters= filters.video | filters.document | filters.audio | filters.photo)
mirror_menu_cb = CallbackQueryHandler(mirror_menu, filters=filters.regex("mirrormenu"))

if AUTO_MIRROR:
    Bot.add_handler(auto_mirror_handler)
Bot.add_handler(mirror_handler)   
Bot.add_handler(zip_mirror_handler)
Bot.add_handler(unzip_mirror_handler)
Bot.add_handler(mirror_menu_cb)

