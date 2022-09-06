from os import listdir, path as ospath
from time import time
from requests import get
from bot import DOWNLOAD_DIR, LOGGER, MEGA_KEY, Bot
from asyncio import TimeoutError
from bot import Bot, DOWNLOAD_DIR, LOGGER, TG_SPLIT_SIZE
from pyrogram import filters
from pyrogram.handlers import CallbackQueryHandler
from subprocess import run
from re import match as re_match
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram import filters
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.bot_utils import get_content_type, is_gdrive_link, is_magnet, is_mega_link, is_url
from bot.helper.ext_utils.direct_link_generator import direct_link_generator
from bot.helper.ext_utils.exceptions import DirectDownloadLinkException
from bot.helper.ext_utils.filters import CustomFilters
from bot.helper.ext_utils.message_utils import editMessage, sendMarkup, sendMessage
from bot.helper.ext_utils.misc_utils import get_readable_size
from bot.helper.ext_utils.rclone_utils import is_not_config, is_not_drive
from bot.helper.ext_utils.var_holder import get_rclone_var, set_rclone_var
from bot.helper.ext_utils.zip_utils import extract_archive
from bot.helper.mirror_leech_utils.download_utils.aria.aria2_download import Aria2Downloader
from bot.helper.mirror_leech_utils.download_utils.mega.mega_download import MegaDownloader
from bot.helper.mirror_leech_utils.download_utils.qbit.qbit_downloader import QbDownloader
from bot.helper.mirror_leech_utils.download_utils.rclone.rclone_mirror import RcloneMirror
from bot.helper.mirror_leech_utils.download_utils.telegram.telegram_downloader import TelegramDownloader
from bot.helper.mirror_leech_utils.upload_utils.telegram.telegram_uploader import TelegramUploader


async def handle_mirror(client, message):
    await mirror_leech(client, message)

async def handle_zip_mirror(client, message):
    await mirror_leech(client, message, isZip=True)

async def handle_unzip_mirror(client, message):
    await mirror_leech(client, message, extract=True)

async def handle_qbit_mirror(client, message):
    await mirror_leech(client, message, isQbit=True)

async def handle_qbit_leech(client, message):
    await mirror_leech(client, message, isLeech=True)

async def mirror_leech(client, message, isZip=False, extract=False, isQbit=False, isLeech= False):
        user_id= message.from_user.id
        if await is_not_config(user_id, message):
            return
        if await is_not_drive(user_id, message):
            return
        reply_message= message.reply_to_message
        select = False
        pswd= None  
        link= ''
        msg = message.text.split(maxsplit=1)
        if len(msg) > 1:
            msgArgs = msg[1].split(maxsplit=1)
            for x in msgArgs:
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
        else:
            tag = message.from_user.first_name

        if reply_message is not None:
            file = reply_message.document or reply_message.video or reply_message.audio or reply_message.photo or None
            if reply_message.from_user.username:
                tag = f"@{reply_message.from_user.username}"
            else:
                tag = reply_message.from_user.first_name    
            if file is None:
                reply_text= reply_message.text     
                if is_url(reply_text) or is_magnet(reply_text):     
                     link = reply_text.strip() 
            elif file.mime_type != "application/x-bittorrent":
                    name= file.file_name
                    size= get_readable_size(file.file_size)
                    header_msg = f"<b>Which name do you want to use?</b>\n\n<b>Name</b>: `{name}`\n\n<b>Size</b>: `{size}`"
                    set_rclone_var("FILE", file, user_id)
                    set_rclone_var("IS_ZIP", isZip, user_id)
                    set_rclone_var("EXTRACT", extract, user_id)
                    set_rclone_var("PSWD", pswd, user_id)
                    keyboard = [[InlineKeyboardButton(f"📄 By default", callback_data= f'mirrormenu_default'),
                            InlineKeyboardButton(f"📝 Rename", callback_data='mirrormenu_rename')],
                            [InlineKeyboardButton("Close", callback_data= f"mirrorsetmenu^close")]]
                    return await sendMarkup(header_msg, message, reply_markup= InlineKeyboardMarkup(keyboard))
            else:
                link = await client.download_media(file)

        if not is_url(link) and not is_magnet(link):
            help_msg = '''
<code>/cmd</code> link

<b>Replying to link</b>   
<code>/cmd</code> link

<b>Replying to file</b>   
<code>/cmd</code> pswd: xx(zip/unzip)

<b>Bittorrent selection:</b>    
<code>/cmd</code> <b>s</b> link or by replying to file/link
            '''
            return await sendMessage(help_msg, message)
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
            gmsg = f"Use /{BotCommands.GcloneCommand} to clone Google Drive file/folder\n\n"
            await sendMessage(gmsg, message)      
        elif is_mega_link(link):
            if MEGA_KEY is not None:
                mega_dl= MegaDownloader(link, message)   
                state, rmsg, path= await mega_dl.execute(path= f'{DOWNLOAD_DIR}{message.id}')
                if state:
                    rclone_mirror = RcloneMirror(path, rmsg, tag, user_id)
                    await rclone_mirror.mirror()
            else:
                await sendMessage("MEGA_API_KEY not provided!", message)
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
                if isLeech:
                    tgUpload = TelegramUploader(path, rmsg)
                    await tgUpload.upload()
                else:     
                    rclone_mirror = RcloneMirror(path, rmsg, tag, user_id)
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
                rclone_mirror= RcloneMirror(path, rmsg, tag, user_id)
                await rclone_mirror.mirror() 

async def mirror_menu(client, query):
    list = query.data.split("_")
    message= query.message
    user_id= str(query.from_user.id)
    tag = f"@{message.reply_to_message.from_user.username}"
    
    file= get_rclone_var("FILE", user_id)
    isZip = get_rclone_var("IS_ZIP", user_id)
    extract = get_rclone_var("EXTRACT", user_id)
    pswd = get_rclone_var("PSWD", user_id) 

    if "default" in list[1]:
        await mirror_file(client, message, file, tag, user_id, pswd, isZip=isZip, extract=extract)

    if "rename" in list[1]: 
        question= await client.send_message(message.chat.id, text= "Send the new name /ignore to cancel")
        try:
            response = await client.listen.Message(filters.text, id= tag, timeout = 30)
        except TimeoutError:
            await question.reply("Cannot wait more longer for your response!")
        else:
            if response:
                if "/ignore" in response.text:
                    await question.reply("Okay cancelled question!")
                    await client.listen.Cancel(tag)
                else:
                    await mirror_file(client, message, file, tag, user_id, pswd, isZip=isZip, extract=extract, new_name=response.text, is_rename=True)
        finally:
            await question.delete()

async def mirror_file(client, message, file, tag, user_id, pswd, isZip, extract, new_name="", is_rename=False):
    msg = await editMessage('Starting download...', message)
    tg_down= TelegramDownloader(file, client, msg, DOWNLOAD_DIR)
    media_path= await tg_down.download() 
    if media_path is None:
        return
    m_path = media_path
    if isZip:
        try:
            base = ospath.basename(m_path)
            file_name = base.rsplit('.', maxsplit=1)[0]
            file_name = file_name + ".zip"
            path = f'{DOWNLOAD_DIR}{file_name}'
            size = ospath.getsize(m_path)
            if pswd is not None:
                if int(size) > TG_SPLIT_SIZE:
                    run(["7z", f"-v{TG_SPLIT_SIZE}b", "a", "-mx=0", f"-p{pswd}", path, m_path])     
                else:
                    run(["7z", "a", "-mx=0", f"-p{pswd}", path, m_path])
            elif int(size) > TG_SPLIT_SIZE:
                run(["7z", f"-v{TG_SPLIT_SIZE}b", "a", "-mx=0", path, m_path])
            else:
                run(["7z", "a", "-mx=0", path, m_path])
        except FileNotFoundError:
            LOGGER.info('File to archive not found!')
            return
    elif extract:
        path= await extract_archive(m_path, message, pswd)
    else:
        path= m_path
    rc_mirror= RcloneMirror(path, msg, tag, user_id, new_name= new_name, is_rename= is_rename)
    await rc_mirror.mirror()   

mirror_handler = MessageHandler(handle_mirror,
        filters=filters.command(BotCommands.MirrorCommand) & CustomFilters.user_filter | CustomFilters.chat_filter)

zip_mirror_handler = MessageHandler(handle_zip_mirror,
        filters=filters.command(BotCommands.ZipMirrorCommand) & CustomFilters.user_filter | CustomFilters.chat_filter)

unzip_mirror_handler = MessageHandler(handle_unzip_mirror,
        filters=filters.command(BotCommands.UnzipMirrorCommand) & CustomFilters.user_filter | CustomFilters.chat_filter)

qbit_mirror_handler = MessageHandler(handle_qbit_mirror,
        filters=filters.command(BotCommands.QbMirrorCommand) & CustomFilters.user_filter | CustomFilters.chat_filter)

qbit_leech_handler = MessageHandler(handle_qbit_leech,
        filters=filters.command(BotCommands.QbLeechCommand) & CustomFilters.user_filter | CustomFilters.chat_filter)

mirror_menu_cb = CallbackQueryHandler(mirror_menu,
        filters=filters.regex("mirrormenu"))

Bot.add_handler(mirror_handler)   
Bot.add_handler(zip_mirror_handler)
Bot.add_handler(unzip_mirror_handler)
Bot.add_handler(qbit_mirror_handler)
Bot.add_handler(qbit_leech_handler)
Bot.add_handler(mirror_menu_cb)

