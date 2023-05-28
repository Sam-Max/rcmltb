from bot import DOWNLOAD_DIR, LOGGER, OWNER_ID, PARALLEL_TASKS, bot, config_dict
from asyncio import Queue, TimeoutError, sleep
from bot import bot, DOWNLOAD_DIR, config_dict, m_queue
from pyrogram import filters
from base64 import b64encode
from os import path as ospath
from re import match as re_match, split as re_split
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.ext_utils.bot_utils import get_content_type, is_gdrive_link, is_magnet, is_mega_link, is_url, new_task, create_task, run_sync
from bot.helper.ext_utils.direct_link_generator import direct_link_generator
from bot.helper.ext_utils.exceptions import DirectDownloadLinkException
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.ext_utils.help_messages import MIRROR_HELP_MESSAGE, MULTIZIP_HELP_MESSAGE
from bot.helper.ext_utils.menu_utils import Menus
from bot.helper.telegram_helper.message_utils import deleteMessage, sendMarkup, sendMessage
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.misc_utils import get_readable_size
from bot.helper.ext_utils.rclone_data_holder import get_rclone_data, update_rclone_data
from bot.helper.ext_utils.rclone_utils import is_rclone_config, is_remote_selected, list_remotes
from bot.helper.mirror_leech_utils.download_utils.aria2_download import add_aria2c_download
from bot.helper.mirror_leech_utils.download_utils.gd_downloader import add_gd_download
from bot.helper.mirror_leech_utils.download_utils.mega_download import add_mega_download
from bot.helper.mirror_leech_utils.download_utils.qbit_downloader import add_qb_torrent
from bot.helper.mirror_leech_utils.download_utils.telegram_downloader import TelegramDownloader
from bot.modules.tasks_listener import MirrorLeechListener


listener_dict = {}


async def handle_mirror(client, message):
    await mirror_leech(client, message)

async def handle_zip_mirror(client, message):
    await mirror_leech(client, message, isZip=True)

async def handle_multizip_mirror(client, message):
    await mirror_leech(client, message, multiZip=True)    

async def handle_unzip_mirror(client, message):
    await mirror_leech(client, message, extract=True)


# Added some modifications from base repo and new features
async def mirror_leech(client, message, isZip=False, extract=False, isLeech=False, multiZip=False):
    
    user_id= message.from_user.id
    if not isLeech:
        if await is_rclone_config(user_id, message):pass
        else: return
        if await is_remote_selected(user_id, message):pass
        else: return
   
    message_id= message.id
    mesg = message.text.split('\n')
    message_args = mesg[0].split(maxsplit=1)
    
    select = False
    multi= 0
    zip_name = ''
    seed = False
    seed_time= None
    ratio= None
    link = ''

    if len(message_args) > 1:
        index = 1
        args = mesg[0].split(maxsplit=4)
        args.pop(0)
        for x in args:
            x = x.strip()
            if x == 's':
                select = True
                index += 1
            elif x == 'd':
                seed = True
                index += 1
            elif x.startswith('d:'):
                seed = True
                index += 1
                dargs = x.split(':')
                ratio = dargs[1] or None
                if len(dargs) == 3:
                    seed_time = dargs[2] or None
            elif x.isdigit():
                multi = int(x)
                mi = index
                index += 1
            elif x.startswith('m:'):
                marg = x.split('m:', 1)
                index += 1
                if len(marg) > 1:
                    zip_name = f"{marg[1]}"
            else:
                break

        if multi == 0:
            message_args = mesg[0].split(maxsplit=index)
            if len(message_args) > index:
                x = message_args[index].strip()
                if not x.startswith(('n:', 'pswd:')):
                    link = re_split(r' pswd: | n: ', x)[0].strip()

        if len(zip_name) > 0:
            seed = False
            ratio = None
            seed_time = None

    @new_task
    async def _run_multi():
        if multi > 1:
            await sleep(4)
            msg = message.text.split(maxsplit=mi+1)
            msg[mi] = f"{multi - 1}"
            nextmsg = await client.get_messages(message.chat.id, message.reply_to_message.id + 1)
            nextmsg = await sendMessage(" ".join(msg), nextmsg)
            nextmsg = await client.get_messages(message.chat.id, nextmsg.id)
            nextmsg.from_user = message.from_user
            await sleep(4)
            await mirror_leech(client, nextmsg, isZip, extract, isLeech, multiZip)

    path = f'{DOWNLOAD_DIR}{message.id}'

    name = mesg[0].split(' n: ', 1)
    if len(name) > 1:
        name= re_split(' pswd: ', name[1])[0].strip()
    else:
        name= ''

    pswd = mesg[0].split(' pswd: ', 1)
    if len(pswd) > 1:
        pswd = re_split(' n: ', pswd[1])[0]
    else:
        pswd = None

    if username := message.from_user.username:
        tag = f"@{username}"
    else:
        tag = message.from_user.mention

   
    file = None
    if reply_message:= message.reply_to_message:
        file = reply_message.document or reply_message.video or reply_message.audio or reply_message.photo or \
               reply_message.voice or reply_message.video_note or reply_message.sticker or reply_message.animation or None
        if len(link) == 0 or not is_url(link) and not is_magnet(link):
            if file is None:
                reply_text = reply_message.text.split('\n', 1)[0].strip()
                if is_url(reply_text) or is_magnet(reply_text):
                    link = reply_text
                _run_multi() 
            elif reply_message.document and (file.mime_type == 'application/x-bittorrent' or file.file_name.endswith('.torrent')):
                link = await reply_message.download()
                file = None
                _run_multi()   

    if link:
        LOGGER.info(link)

    if not is_url(link) and not is_magnet(link) and not ospath.exists(link) and file is None:
        if multiZip:
            await sendMessage(MULTIZIP_HELP_MESSAGE, message)
        else:
            await sendMessage(MIRROR_HELP_MESSAGE, message)
        return

    if not is_mega_link(link) and not is_magnet(link) and not is_gdrive_link(link) \
        and not link.endswith('.torrent') and file is None:
        content_type = await run_sync(get_content_type, link)
        if content_type is None or re_match(r'text/html|text/plain', content_type):
            try:
                link = await run_sync(direct_link_generator, link) 
            except DirectDownloadLinkException as e:
                if str(e).startswith('ERROR:'):
                    await sendMessage(str(e), message)
                    return

    listener= MirrorLeechListener(message, tag, user_id, isZip, extract, pswd, 
                                  select, seed, isLeech, multiZip, zip_name)   

    if file is not None:
        if multiZip:
            tg_down= TelegramDownloader(file, client, listener, f'{DOWNLOAD_DIR}{zip_name}/', name, multi)
            await tg_down.download() 
            _run_multi() 
        elif multi:
            tg_down= TelegramDownloader(file, client, listener, f'{path}/', name)
            if PARALLEL_TASKS:    
                await m_queue.put(tg_down)
            else:
                tg_down.download()
            _run_multi() 
        else:
            buttons= ButtonMaker() 
            file_name= file.file_name
            size= get_readable_size(file.file_size)
            header_msg = f"Which name do you want to use?\n\n<b>Name</b>: <code>{file_name}</code>\n\n<b>Size</b>: <code>{size}</code>"
            buttons.cb_buildbutton("📄 By default", f"mirrormenu^default")
            buttons.cb_buildbutton("📝 Rename", f"mirrormenu^rename")
            buttons.cb_buildbutton("✘ Close Menu", f"mirrormenu^close", 'footer')
            listener_dict[message_id] = [listener, file, message, isLeech, user_id]
            await sendMarkup(header_msg, message, reply_markup= buttons.build_menu(2))
            return
    elif is_gdrive_link(link):
        await add_gd_download(link, path, listener, name)   
    elif is_mega_link(link):
        await add_mega_download(link, f'{path}/', listener, name)
    elif is_magnet(link) or ospath.exists(link):
        await add_qb_torrent(link, path, listener, ratio, seed_time)
    else:
        if len(mesg) > 1:
            ussr = mesg[1]
            pssw = mesg[2] if len(mesg) > 2 else ''
            auth = f"{ussr}:{pssw}"
            auth = "Basic " + b64encode(auth.encode()).decode('ascii')
        else:
            auth = ''
        await add_aria2c_download(link, path, listener, name, auth)

            
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

    if int(info[-1]) != user_id:
        await query.answer("This menu is not for you!", show_alert=True)
        return
    elif cmd[1] == "default" :
        await query_message.delete()
        if config_dict['REMOTE_SELECTION'] and not is_Leech:
            update_rclone_data('NAME', "", user_id) 
            await list_remotes(message, menu_type=Menus.REMOTE_SELECT)    
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
                    await client.listen.Cancel(filters.user(user_id))
                else:
                    name = response.text.strip()
                    if config_dict['REMOTE_SELECTION'] and not is_Leech:
                        update_rclone_data('NAME', name, user_id) 
                        await list_remotes(message, menu_type= Menus.REMOTE_SELECT)   
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
        update_rclone_data("MIRROR_SELECT_BASE_DIR", "", user_id)
        update_rclone_data("MIRROR_SELECT_REMOTE", cmd[2], user_id)
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
    file = message.document or message.video or message.audio or message.photo or \
           message.voice or message.video_note or message.sticker or message.animation or None
    if username := message.from_user.username:
        tag = f"@{username}"
    else:
        tag = message.from_user.mention
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
    LOGGER.info("Creating parallel tasks")
    for i in range(PARALLEL_TASKS):
        create_task(worker, m_queue)

mirror_handler = MessageHandler(handle_mirror,filters=filters.command(BotCommands.MirrorCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter))
zip_mirror_handler = MessageHandler(handle_zip_mirror,filters=filters.command(BotCommands.ZipMirrorCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter))
unzip_mirror_handler = MessageHandler(handle_unzip_mirror,filters=filters.command(BotCommands.UnzipMirrorCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter))
multizip_mirror_handler = MessageHandler(handle_multizip_mirror, filters=filters.command(BotCommands.MultiZipMirrorCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter))
auto_mirror_handler = MessageHandler(handle_auto_mirror, filters= filters.video | filters.document | filters.audio | filters.photo)
mirror_menu_cb = CallbackQueryHandler(mirror_menu, filters=filters.regex("mirrormenu"))
mirror_select_cb = CallbackQueryHandler(mirror_select, filters=filters.regex("remoteselectmenu"))

if config_dict['AUTO_MIRROR']:
    bot.add_handler(auto_mirror_handler)
bot.add_handler(mirror_handler)   
bot.add_handler(zip_mirror_handler)
bot.add_handler(multizip_mirror_handler)
bot.add_handler(unzip_mirror_handler)
bot.add_handler(mirror_menu_cb)
bot.add_handler(mirror_select_cb)

