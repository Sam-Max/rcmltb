from asyncio import sleep
from yt_dlp import YoutubeDL
from aiohttp import ClientSession
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.filters import regex, command
from bot import DOWNLOAD_DIR, LOGGER, config_dict, user_data, bot
from re import split as re_split
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.ext_utils.bot_utils import is_url, new_task, run_sync
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.ext_utils.help_messages import YT_HELP_MESSAGE
from bot.helper.ext_utils.human_format import get_readable_file_size
from bot.helper.telegram_helper.message_utils import editMessage, sendMessage
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.rclone_utils import is_rclone_config, is_remote_selected
from bot.helper.mirror_leech_utils.download_utils.yt_dlp_helper import YoutubeDLHelper
from bot.modules.tasks_listener import MirrorLeechListener


ytdl_dict = {}


#Some refactoring from source
async def select_format(_, query):
    data = query.data.split()
    message = query.message
    user_id= query.from_user.id
    qual = None
    await query.answer()

    try:
        task_info= ytdl_dict[user_id]
    except:
        await editMessage("This is an old task", message)
        return

    listener = task_info[0]
    link= task_info[1]
    path= task_info[2]
    name= task_info[3]
    opt= task_info[4]
    formats= task_info[5]
    is_playlist= task_info[6]

    if data[1] == 'dict':
        b_name = data[2]
        await qual_subbuttons(message, formats, b_name)
    elif data[1] == 'mp3':
        await mp3_subbuttons(message, is_playlist)
    elif data[1] == 'audio':
        await audio_format(message, is_playlist )
    elif data[1] == 'aq':
        if data[2] == 'back':
            await audio_format(message, is_playlist)
        else:
            await audio_quality(message, data[2], is_playlist)
    elif data[1] == 'cancel':
        await editMessage('Task has been cancelled.', message)
        qual = None
    else:
        if data[1] == 'sub':
            qual = formats[data[2]][data[3]][1]
        elif '|' in data[1]:
            qual = formats[data[1]]
        else:
            qual = data[1]

        del ytdl_dict[user_id]
        await message.delete()
        
        LOGGER.info(f'Downloading with YT-DLP')
        ydl = YoutubeDLHelper(listener)
        await ydl.add_download(link, path, name, qual, is_playlist, opt)    

async def select_quality(message, result, listener, link, path, name, opt):
    is_playlist = False
    is_m4a = False
    formats = {}
    
    buttons = ButtonMaker()
    if 'entries' in result:
        for i in ['144', '240', '360', '480', '720', '1080', '1440', '2160']:
            video_format = f'bv*[height<=?{i}][ext=mp4]+ba[ext=m4a]/b[height<=?{i}]'
            b_data = f'{i}|mp4'
            formats[b_data] = video_format
            buttons.cb_buildbutton(f'{i}-mp4', f'ytq {b_data}')
            video_format = f'bv*[height<=?{i}][ext=webm]+ba/b[height<=?{i}]'
            b_data = f'{i}|webm'
            formats[b_data] = video_format
            buttons.cb_buildbutton(f'{i}-webm', f'ytq {b_data}')
        buttons.cb_buildbutton('MP3', 'ytq mp3')
        buttons.cb_buildbutton('Audio Formats', 'ytq audio')
        buttons.cb_buildbutton('Best Videos', 'ytq bv*+ba/b')
        buttons.cb_buildbutton('Best Audios', 'ytq ba/b')
        buttons.cb_buildbutton('Cancel', 'ytq cancel', 'footer')
        main_buttons = buttons.build_menu(3)
        msg = f'Choose Playlist Videos Quality:\n'
    else:
        format_dict = result.get('formats')
        if format_dict is not None:
            for item in format_dict:
                if item.get('tbr'):
                    format_id = item['format_id']

                    if item.get('filesize'):
                        size = item['filesize']
                    elif item.get('filesize_approx'):
                        size = item['filesize_approx']
                    else:
                        size = 0

                    if item.get('video_ext') == 'none' and item.get('acodec') != 'none':
                        if item.get('audio_ext') == 'm4a':
                            is_m4a = True
                        b_name = f"{item['acodec']}-{item['ext']}"
                        v_format = f'ba[format_id={format_id}]'
                    elif item.get('height'):
                        height = item['height']
                        ext = item['ext']
                        fps = item['fps'] if item.get('fps') else ''
                        b_name = f'{height}p{fps}-{ext}'
                        ba_ext = '[ext=m4a]' if is_m4a and ext == 'mp4' else ''
                        v_format = f'bv*[format_id={format_id}]+ba{ba_ext}/b[height=?{height}]'
                    else:
                        continue

                    formats.setdefault(b_name, {})[f"{item['tbr']}"] = [
                        size, v_format]

            for b_name, tbr_dict in formats.items():
                if len(tbr_dict) == 1:
                    tbr, v_list = next(iter(tbr_dict.items()))
                    buttonName = f'{b_name} ({get_readable_file_size(v_list[0])})'
                    buttons.cb_buildbutton(buttonName, f'ytq sub {b_name} {tbr}')
                else:
                    buttons.cb_buildbutton(b_name, f'ytq dict {b_name}')
        buttons.cb_buildbutton('MP3', 'ytq mp3')
        buttons.cb_buildbutton('Audio Formats', 'ytq audio')
        buttons.cb_buildbutton('Best Video', 'ytq bv*+ba/b')
        buttons.cb_buildbutton('Best Audio', 'ytq ba/b')
        buttons.cb_buildbutton('Cancel', 'ytq cancel', 'footer')
        main_buttons = buttons.build_menu(2)

        ytdl_dict[message.from_user.id] = [listener, link, path, name, opt, formats, is_playlist]
        msg = f'Choose Video Quality:\n'
        await sendMessage(msg, message, main_buttons)

async def qual_subbuttons(message, formats, b_name):
    buttons = ButtonMaker()
    tbr_dict = formats[b_name]
    for tbr, d_data in tbr_dict.items():
        button_name = f'{tbr}K ({get_readable_file_size(d_data[0])})'
        buttons.cb_buildbutton(button_name, f'ytq sub {b_name} {tbr}')
    buttons.cb_buildbutton('Back', 'ytq back', 'footer')
    buttons.cb_buildbutton('Cancel', 'ytq cancel', 'footer')
    subbuttons = buttons.build_menu(2)
    msg = f'Choose Bit rate for <b>{b_name}</b>:\n'
    await editMessage(msg, message, subbuttons)

async def mp3_subbuttons(message, is_playlist):
    i = 's' if is_playlist else ''
    buttons = ButtonMaker()
    audio_qualities = [64, 128, 320]
    for q in audio_qualities:
        audio_format = f'ba/b-mp3-{q}'
        buttons.cb_buildbutton(f'{q}K-mp3', f'ytq {audio_format}')
    buttons.cb_buildbutton('Back', 'ytq back')
    buttons.cb_buildbutton('Cancel', 'ytq cancel')
    subbuttons = buttons.build_menu(3)
    msg = f'Choose mp3 Audio{i} Bitrate:\nTimeout:'
    await editMessage(msg, message, subbuttons)

async def audio_format(message, is_playlist):
    i = 's' if is_playlist else ''
    buttons = ButtonMaker()
    for frmt in ['aac', 'alac', 'flac', 'm4a', 'opus', 'vorbis', 'wav']:
        audio_format = f'ba/b-{frmt}-'
        buttons.cb_buildbutton(frmt, f'ytq aq {audio_format}')
    buttons.cb_buildbutton('Back', 'ytq back', 'footer')
    buttons.cb_buildbutton('Cancel', 'ytq cancel', 'footer')
    subbuttons = buttons.build_menu(3)
    msg = f'Choose Audio{i} Format:\n'
    await editMessage(msg, message, subbuttons)

async def audio_quality(message, format, is_playlist):
    i = 's' if is_playlist else ''
    buttons = ButtonMaker()
    for qual in range(11):
        audio_format = f'{format}{qual}'
        buttons.cb_buildbutton(qual, f'ytq {audio_format}')
    buttons.cb_buildbutton('Back', 'ytq aq back')
    buttons.cb_buildbutton('Cancel', 'ytq aq cancel')
    subbuttons = buttons.build_menu(5)
    msg = f'Choose Audio{i} Qaulity:\n0 is best and 10 is worst\n'
    await editMessage(msg, message, subbuttons)

def extract_info(link, options):
    with YoutubeDL(options) as ydl:
        result = ydl.extract_info(link, download=False)
        if result is None:
            raise ValueError('Info result is None')
        return result

async def _mdisk(link, name):
    key = link.split('/')[-1]
    async with ClientSession() as session:
        async with session.get(f'https://diskuploader.entertainvideo.com/v1/file/cdnurl?param={key}') as resp:
            if resp.status == 200:
                resp_json = await resp.json()
                link = resp_json['source']
                if not name:
                    name = resp_json['filename']
            return name, link      
          

@new_task
async def _ytdl(client, message, isZip= False, isLeech=False):
    mssg = message.text
    user_id = message.from_user.id
    qual = ''
    select = False
    multi = 0
    link = ''
    folder_name = ''
    tag= ''

    if not isLeech:
        if await is_rclone_config(user_id, message): pass
        else: return 
        if await is_remote_selected(user_id, message): pass
        else: return

    args = mssg.split(maxsplit=3)
    args.pop(0)
    if len(args) > 0:
        index = 1
        for x in args:
            x = x.strip()
            if x == 's':
                select = True
                index += 1
            elif x.strip().isdigit():
                multi = int(x)
                mi = index
            else:
                break
        if multi == 0:
            args = mssg.split(maxsplit=index)
            if len(args) > index:
                x = args[index].strip()
                if not x.startswith(('n:', 'pswd:', 'up:', 'rcf:', 'opt:')):
                    link = re_split(r' opt: | pswd: | n: | rcf: | up: ', x)[
                        0].strip()
    
    @new_task
    async def __run_multi():
        if multi <= 1:
            return
        await sleep(4)
        nextmsg = await client.get_messages(chat_id=message.chat.id, message_ids=message.reply_to_message_id + 1)
        ymsg = mssg.split(maxsplit=mi+1)
        ymsg[mi] = f'{multi - 1}'
        nextmsg = await sendMessage(' '.join(ymsg), nextmsg)
        nextmsg = await client.get_messages(chat_id=message.chat.id, message_ids=nextmsg.id)
        nextmsg.from_user = message.from_user
        await sleep(4)
        _ytdl(client, nextmsg, isZip, isLeech)

    path = f'{DOWNLOAD_DIR}{message.id}{folder_name}'
    
    name = mssg.split(' n: ', 1)
    name = re_split(' pswd: | opt: | up: | rcf: ', name[1])[
        0].strip() if len(name) > 1 else ''

    pswd = mssg.split(' pswd: ', 1)
    pswd = re_split(' n: | opt: | up: | rcf: ', pswd[1])[
        0] if len(pswd) > 1 else None

    opt = mssg.split(' opt: ', 1)
    opt = re_split(' n: | pswd: | up: | rcf: ', opt[1])[
        0].strip() if len(opt) > 1 else ''

    opt = opt or config_dict['YT_DLP_OPTIONS']

    if username := message.from_user.username:
        tag = f'@{username}'
    else:
        tag = message.from_user.mention

    if reply_to := message.reply_to_message:
        if len(link) == 0:
            link = reply_to.text.split('\n', 1)[0].strip()
        if not reply_to.from_user.is_bot:
            if username := reply_to.from_user.username:
                tag = f'@{username}'
            else:
                tag = reply_to.from_user.mention

    if not is_url(link):
        await sendMessage(YT_HELP_MESSAGE, message)
        return
    
    listener = MirrorLeechListener(message, tag, user_id, isZip=isZip, pswd=pswd, 
                                   isLeech=isLeech)
    if 'mdisk.me' in link:
        name, link = await _mdisk(link, name)

    options = {'usenetrc': True, 'cookiefile': 'cookies.txt'}
    if opt:
        yt_opt = opt.split('|')
        for ytopt in yt_opt:
            key, value = map(str.strip, ytopt.split(':', 1))
            if value.startswith('^'):
                if '.' in value or value == '^inf':
                    value = float(value.split('^')[1])
                else:
                    value = int(value.split('^')[1])
            elif value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            elif value.startswith(('{', '[', '(')) and value.endswith(('}', ']', ')')):
                value = eval(value)
            options[key] = value

        options['playlist_items'] = '0'
    
    try:
        result = await run_sync(extract_info, link, options)
    except Exception as e:
        msg = str(e).replace('<', ' ').replace('>', ' ')
        await sendMessage(f'{tag} {msg}', message)
        __run_multi()
        return

    __run_multi()
    
    if not select:
        user_dict = user_data.get(user_id, {})
        if 'format' in options:
            qual = options['format']
        elif user_dict.get('yt_opt'):
            qual = user_dict['yt_opt']

    if qual:
        LOGGER.info(f'Downloading with YT-DLP')
        playlist = 'entries' in result
        ydl = YoutubeDLHelper(listener)
        await ydl.add_download(link, path, name, qual, playlist, opt)  
    else:
        await select_quality(message, result, listener, link, path, name, opt)


async def ytdlmirror(client, message):
    await _ytdl(client, message)

async def ytdlzipmirror(client, message):
    await _ytdl(client, message, isZip= True)

async def ytdlleech(client, message):
    await _ytdl(client, message, isLeech=True)    

async def ytdlzipleech(client, message):
    await _ytdl(client, message, isZip= True, isLeech=True)    




bot.add_handler(MessageHandler(ytdlmirror, filters= command(BotCommands.YtdlMirrorCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter)))
bot.add_handler(MessageHandler(ytdlleech, filters= command(BotCommands.YtdlLeechCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter)))
bot.add_handler(MessageHandler(ytdlzipmirror, filters= command(BotCommands.YtdlZipMirrorCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter)))
bot.add_handler(MessageHandler(ytdlzipleech, filters= command(BotCommands.YtdlZipLeechCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter)))
bot.add_handler(CallbackQueryHandler(select_format, filters= regex('^ytq')))


