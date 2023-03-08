from base64 import b64encode
from os import path as ospath
from time import time
from requests import get
from bot import DOWNLOAD_DIR, LOGGER, OWNER_ID, PARALLEL_TASKS, bot, config_dict
from asyncio import Queue, TimeoutError, sleep
from bot import bot, DOWNLOAD_DIR, botloop, config_dict, m_queue
from pyrogram import filters
from re import match as re_match, split as re_split
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.bot_utils import get_content_type, is_gdrive_link, is_magnet, is_mega_link, is_url, run_async, run_async_task, run_sync
from bot.helper.ext_utils.direct_link_generator import direct_link_generator
from bot.helper.ext_utils.exceptions import DirectDownloadLinkException
from bot.helper.ext_utils.filters import CustomFilters
from bot.helper.ext_utils.message_utils import deleteMessage, sendMarkup, sendMessage
from bot.helper.ext_utils.button_build import ButtonMaker
from bot.helper.ext_utils.misc_utils import get_readable_size
from bot.helper.ext_utils.rclone_data_holder import get_rclone_data, update_rclone_data
from bot.helper.ext_utils.rclone_utils import is_rclone_config, is_remote_selected, list_remotes
from bot.helper.mirror_leech_utils.download_utils.aria2_download import add_aria2c_download
from bot.helper.mirror_leech_utils.download_utils.gd_downloader import add_gd_download
from bot.helper.mirror_leech_utils.download_utils.mega_download import add_mega_download
from bot.helper.mirror_leech_utils.download_utils.qbit_downloader import add_qb_torrent
from bot.helper.mirror_leech_utils.download_utils.telegram_downloader import TelegramDownloader
from bot.modules.listener import MirrorLeechListener


listener_dict = {}



async def handle_mirror(client, message):
    await mirror_leech(client, message)

async def handle_zip_mirror(client, message):
    await mirror_leech(client, message, isZip=True)

async def handle_multizip_mirror(client, message):
    await mirror_leech(client, message, multiZip=True)    

async def handle_unzip_mirror(client, message):
    await mirror_leech(client, message, extract=True)


# Source: https://github.com/anasty17/mirror-leech-telegram-bot/blob/master/bot/modules/mirror_leech.py
# Adapted for asyncio/pyrogram with rclone with minor modifications 
async def mirror_leech(client, message, isZip=False, extract=False, isLeech=False, multiZip=False):
    user_id= message.from_user.id
    message_id= message.id
    mesg = message.text.split('\n')
    message_args = mesg[0].split(maxsplit=1)
    name_args = mesg[0].split('|', maxsplit=1)
    if not isLeech:
        if await is_rclone_config(user_id, message):
            pass
        else: 
            return
        if await is_remote_selected(user_id, message):
            pass
        else: 
            return
    select = False
    index = 1
    multi= 0
    tag= ''
    if len(message_args) > 1:
        args = mesg[0].split(maxsplit=3)
        for x in args:
            x = x.strip()
            if x in ['|', 'pswd:']:
                break
            elif x == 's':
                select = True
                index += 1
            elif x.isdigit():
                multi = int(x)
                mi = index
        if multi == 0:
            message_args = mesg[0].split(maxsplit=index)
            if len(message_args) > index:
                link = message_args[index].strip()
                if link.startswith(("|", "pswd:")):
                    link = ''
            else:
                link = ''
        else:
            link = ''
    else:
        link = ''

    if len(name_args) > 1:
        name = name_args[1]
        name = name.split(' pswd:')[0]
        name = name.strip()
    else:
        name = ''

    link = re_split(r"pswd:|\|", link)[0]
    link = link.strip()

    pswd_arg = mesg[0].split(' pswd: ')
    if len(pswd_arg) > 1:
        pswd = pswd_arg[1]
    else:
        pswd = None

    if message.from_user.username:
        tag = f"@{message.from_user.username}"

    if reply_message:= message.reply_to_message:
        listener= MirrorLeechListener(message, tag, user_id, isZip=isZip, isMultiZip=multiZip, extract=extract, pswd=pswd, isLeech=isLeech)
        file = reply_message.document or reply_message.video or reply_message.audio or reply_message.photo or \
               reply_message.voice or reply_message.video_note or reply_message.sticker or reply_message.animation or None
        if reply_message.from_user.username:
            tag = f"@{reply_message.from_user.username}"
        if len(link) == 0 or not is_url(link) and not is_magnet(link):
            if file is None:
                reply_text= reply_message.text.split(maxsplit=1)[0].strip()     
                if is_url(reply_text) or is_magnet(reply_text):     
                    link = reply_text
            elif file.mime_type != "application/x-bittorrent":
                if multi and multiZip:
                    tg_down= TelegramDownloader(file, client, listener, f'{DOWNLOAD_DIR}{listener.user_id}/multizip/', name, multi, multi_zip=multiZip)
                    await tg_down.download() 
                    if multi > 1:
                        await sleep(4)
                        nextmsg = await client.get_messages(message.chat.id, message.reply_to_message.id + 1)
                        msg = message.text.split(maxsplit=mi+1)
                        msg[mi] = f"{multi - 1}"
                        nextmsg = await sendMessage(" ".join(msg), nextmsg)
                        nextmsg = await client.get_messages(message.chat.id, nextmsg.id)
                        nextmsg.from_user.id = message.from_user.id
                        await sleep(4)
                        await mirror_leech(client, nextmsg, isLeech=isLeech, multiZip=multiZip)
                elif multi:
                    tg_down= TelegramDownloader(file, client, listener, f'{DOWNLOAD_DIR}{listener.uid}/', name)
                    if PARALLEL_TASKS:    
                        await m_queue.put(tg_down)
                    else:
                        await run_async_task(tg_down.download)
                    if multi > 1:
                        await sleep(4)
                        nextmsg = await client.get_messages(message.chat.id, message.reply_to_message.id + 1)
                        msg = message.text.split(maxsplit=mi+1)
                        msg[mi] = f"{multi - 1}"
                        nextmsg = await sendMessage(" ".join(msg), nextmsg)
                        nextmsg = await client.get_messages(message.chat.id, nextmsg.id)
                        nextmsg.from_user.id = message.from_user.id
                        await sleep(4)
                        await mirror_leech(client, nextmsg, isZip= isZip, extract=extract, isLeech=isLeech)
                else:
                    buttons= ButtonMaker() 
                    file_name= file.file_name
                    size= get_readable_size(file.file_size)
                    header_msg = f"Which name do you want to use?\n\n<b>Name</b>: <code>{file_name}</code>\n\n<b>Size</b>: <code>{size}</code>"
                    buttons.cb_buildbutton("📄 By default", f"mirrormenu^default")
                    buttons.cb_buildbutton("📝 Rename", f"mirrormenu^rename")
                    buttons.cb_buildbutton("✘ Close Menu", f"mirrormenu^close", 'footer')
                    await sendMarkup(header_msg, message, reply_markup= buttons.build_menu(2))
                    listener_dict[message_id] = [listener, file, message, isLeech, user_id]
                return
            else:
                link = await client.download_media(file)
    
    if not is_url(link) and not is_magnet(link) and not ospath.exists(link):
        if multiZip:
             help_msg = '''
<b>Multi zip by replying to first file:</b>

<code>/cmd</code> 5(number of files)
Number should be always before | zipname
             '''
        else:
             help_msg = '''         
<code>/cmd</code> link |newname pswd: xx(zip/unzip)

<b>By replying</b>   
<code>/cmd</code> |newname pswd: xx(zip/unzip)

<b>Direct link authorization:</b>
<code>/cmd</code> link |newname pswd: xx(zip/unzip)
<b>username</b>
<b>password</b>

<b>qBittorrent Selection</b>    
<code>/cmd</code> <b>s</b> link or by replying to link

<b>Multi links by replying to first link/file:</b>
<code>/cmd</code> 5(number of links/files)
Number should be always before |newname or pswd:
                '''
        return await sendMessage(help_msg, message)

    listener= MirrorLeechListener(message, tag, user_id, isZip=isZip, extract=extract, pswd=pswd, select=select, isLeech=isLeech)

    if not is_mega_link(link) and not is_magnet(link) and not is_gdrive_link(link) \
        and not link.endswith('.torrent'):
        content_type = await run_sync(get_content_type, link)
        if content_type is None or re_match(r'text/html|text/plain', content_type):
            try:
                link = await run_sync(direct_link_generator, link) 
            except DirectDownloadLinkException as e:
                if str(e).startswith('ERROR:'):
                    return await sendMessage(str(e), message)
    elif not is_magnet(link) and not ospath.exists(link):
        if link.endswith('.torrent'):
            content_type = None
        else:
            content_type = await run_sync(get_content_type, link)
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
        await add_gd_download(link, f'{DOWNLOAD_DIR}{listener.uid}', listener, name)   
    elif is_mega_link(link):
        await add_mega_download(link, f'{DOWNLOAD_DIR}{listener.uid}/', listener, name)
    elif is_magnet(link) or ospath.exists(link):
        await add_qb_torrent(link, f'{DOWNLOAD_DIR}{listener.uid}', listener)
    else:
        if len(mesg) > 1:
            ussr = mesg[1]
            if len(mesg) > 2:
                pssw = mesg[2]
            else:
                pssw = ''
            auth = f"{ussr}:{pssw}"
            auth = "Basic " + b64encode(auth.encode()).decode('ascii')
        else:
            auth = ''
        await add_aria2c_download(link, f'{DOWNLOAD_DIR}{listener.uid}', listener, name, auth)

    if multi > 1:
        await sleep(4)
        nextmsg = await client.get_messages(message.chat.id, message.reply_to_message.id + 1)
        msg = message.text.split(maxsplit=mi+1)
        msg[mi] = f"{multi - 1}"
        nextmsg = await sendMessage(" ".join(msg), nextmsg)
        nextmsg = await client.get_messages(message.chat.id, nextmsg.id)
        nextmsg.from_user.id = message.from_user.id
        await sleep(4)
        await mirror_leech(client, nextmsg, isZip= isZip, extract=extract, isLeech=isLeech)

async def mirror_menu(client, query):
    cmd = query.data.split("^")
    query_message= query.message
    reply_message= query_message.reply_to_message
    user_id= query.from_user.id
    message_id= reply_message.id
    info= listener_dict[message_id] 
    listener= info[0]
    file = info[1]
    message= info[2]
    is_Leech= info[3]
    rclone_remote = get_rclone_data("CLOUDSEL_REMOTE", user_id)
    base_dir= get_rclone_data("CLOUDSEL_BASE_DIR", user_id)

    if int(info[-1]) != user_id:
        await query.answer("This menu is not for you!", show_alert=True)
        return
    elif cmd[1] == "default" :
        await query_message.delete()
        if config_dict['REMOTE_SELECTION'] and not is_Leech:
            update_rclone_data('NAME', "", user_id) 
            await list_remotes(message, rclone_remote, base_dir, "mirrorselect")    
        else:
            tg_down= TelegramDownloader(file, client, listener, f'{DOWNLOAD_DIR}{listener.uid}/', "")
            if PARALLEL_TASKS:    
                await m_queue.put(tg_down)
                await query.answer()
            else:
                await tg_down.download() 
    elif cmd[1] == "rename": 
        await query_message.delete()
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
                    name = response.text.strip()
                    if config_dict['REMOTE_SELECTION'] and not is_Leech:
                        update_rclone_data('NAME', name, user_id) 
                        await list_remotes(message, rclone_remote, base_dir, "mirrorselect")   
                    else:
                        tg_down= TelegramDownloader(file, client, listener, f'{DOWNLOAD_DIR}{listener.uid}/', name)
                        if PARALLEL_TASKS:    
                            await query.answer()
                            await m_queue.put(tg_down)
                        else:
                            await tg_down.download() 
        finally:
            await question.delete()
    else:
        await query.answer()
        await query_message.delete()

async def mirror_select(client, callback_query):
    query= callback_query
    data = query.data
    cmd = data.split("^")
    message = query.message
    user_id= query.from_user.id
    message_id= int(cmd[-1])
    info= listener_dict[message_id] 
    listener= info[0]
    file = info[1]
    
    if int(info[-1]) != user_id:
        await query.answer("This menu is not for you!", show_alert=True)
        return
    elif cmd[1] == "remote":
        await deleteMessage(message) 
        update_rclone_data("CLOUDSEL_BASE_DIR", "/", user_id)
        update_rclone_data("CLOUDSEL_REMOTE", cmd[2], user_id)
        if user_id == OWNER_ID:
            config_dict.update({'DEFAULT_OWNER_REMOTE': cmd[2]}) 
        name= get_rclone_data("NAME", user_id)
        tg_down= TelegramDownloader(file, client, listener, f'{DOWNLOAD_DIR}{listener.uid}/', name)
        if PARALLEL_TASKS:    
            await m_queue.put(tg_down)
            await query.answer()
        else:
            await tg_down.download() 
        await query.answer()
    elif cmd[1] == "close":
        await query.answer()
        await deleteMessage(message) 
    del listener_dict[message_id]

async def handle_auto_mirror(client, message):
    user_id= message.from_user.id
    if await is_rclone_config(user_id, message) == False:
        return
    if await is_remote_selected(user_id, message) == False:
        return
    file = message.document or message.video or message.audio or message.photo or None
    tag = f"@{message.from_user.username}"
    if file is not None:
        if file.mime_type != "application/x-bittorrent":
            listener= MirrorLeechListener(message, tag, user_id)
            tg_down= TelegramDownloader(file, client, listener, f'{DOWNLOAD_DIR}{listener.uid}/', "")
            if PARALLEL_TASKS:    
                await m_queue.put(tg_down)
            else:
                await tg_down.download()  

async def worker(queue: Queue):
    while True:
        tg_down = await queue.get()
        await tg_down.download()
        
# Create worker tasks to process the queue concurrently.        
if PARALLEL_TASKS:
    LOGGER.info("Creating worker tasks")
    for i in range(PARALLEL_TASKS):
        task = botloop.create_task(worker(m_queue))

mirror_handler = MessageHandler(handle_mirror,filters=filters.command(BotCommands.MirrorCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter))
zip_mirror_handler = MessageHandler(handle_zip_mirror,filters=filters.command(BotCommands.ZipMirrorCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter))
unzip_mirror_handler = MessageHandler(handle_unzip_mirror,filters=filters.command(BotCommands.UnzipMirrorCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter))
multizip_mirror_handler = MessageHandler(handle_multizip_mirror, filters=filters.command(BotCommands.MultiZipMirrorCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter))
auto_mirror_handler = MessageHandler(handle_auto_mirror, filters= filters.video | filters.document | filters.audio | filters.photo)
mirror_menu_cb = CallbackQueryHandler(mirror_menu, filters=filters.regex("mirrormenu"))
mirror_select_cb = CallbackQueryHandler(mirror_select, filters=filters.regex("mirrorselect"))

if config_dict['AUTO_MIRROR']:
    bot.add_handler(auto_mirror_handler)
bot.add_handler(mirror_handler)   
bot.add_handler(zip_mirror_handler)
bot.add_handler(multizip_mirror_handler)
bot.add_handler(unzip_mirror_handler)
bot.add_handler(mirror_menu_cb)
bot.add_handler(mirror_select_cb)

