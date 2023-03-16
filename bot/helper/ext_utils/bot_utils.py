# Source: https://github.com/anasty17/mirror-leech-telegram-bot/blob/master/generate_drive_token.py
# Adapted for asyncio framework and pyrogram library

from asyncio import create_subprocess_exec, create_subprocess_shell, run_coroutine_threadsafe, sleep, get_running_loop
from asyncio.subprocess import PIPE
from concurrent.futures import ThreadPoolExecutor
from functools import partial, wraps
from html import escape
from math import ceil
from time import time
from re import IGNORECASE, compile, match as re_match, search
from psutil import cpu_percent, disk_usage, virtual_memory
from bot import DOWNLOAD_DIR, status_dict_lock, status_dict, botUptime, config_dict, user_data, m_queue, botloop
from requests import head as rhead, utils as rutils
from threading import Thread
from urllib.request import urlopen
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.button_build import ButtonMaker
from bot.helper.ext_utils.human_format import get_readable_file_size
from bot.helper.mirror_leech_utils.status_utils.status_utils import MirrorStatus, TaskType, get_progress_bar_rclone, get_progress_bar_string


MAGNET_REGEX = r'magnet:\?xt=urn:(btih|btmh):[a-zA-Z0-9]*\s*'
URL_REGEX = r'^(?!\/)(rtmps?:\/\/|mms:\/\/|rtsp:\/\/|https?:\/\/|ftp:\/\/)?([^\/:]+:[^\/@]+@)?(www\.)?(?=[^\/:\s]+\.[^\/:\s]+)([^\/:\s]+\.[^\/:\s]+)(:\d+)?(\/[^#\s]*[\s\S]*)?(\?[^#\s]*)?(#.*)?$'
SIZE_UNITS = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']

COUNT = 0
PAGE_NO = 1
PAGES = 0

ARCH_EXT = [".tar.bz2", ".tar.gz", ".bz2", ".gz", ".tar.xz", ".tar", ".tbz2", ".tgz", ".lzma2",
            ".zip", ".7z", ".z", ".rar", ".iso", ".wim", ".cab", ".apm", ".arj", ".chm",
            ".cpio", ".cramfs", ".deb", ".dmg", ".fat", ".hfs", ".lzh", ".lzma", ".mbr",
            ".msi", ".mslz", ".nsis", ".ntfs", ".rpm", ".squashfs", ".udf", ".vhd", ".xar"]

FIRST_SPLIT_REGEX = r'(\.|_)part0*1\.rar$|(\.|_)7z\.0*1$|(\.|_)zip\.0*1$|^(?!.*(\.|_)part\d+\.rar$).*\.rar$'

SPLIT_REGEX = r'\.r\d+$|\.7z\.\d+$|\.z\d+$|\.zip\.\d+$'


def is_first_archive_split(file):
    return bool(search(FIRST_SPLIT_REGEX, file))

def is_archive(file):
    return file.endswith(tuple(ARCH_EXT))

def is_archive_split(file):
    return bool(search(SPLIT_REGEX, file))

def is_url(url):
    url = re_match(URL_REGEX, url)
    return bool(url)

def is_gdrive_link(url):
    return "drive.google.com" in url

def is_mega_link(url):
    return "mega.nz" in url or "mega.co.nz" in url

def get_mega_link_type(url):
    if "folder" in url:
        return "folder"
    elif "file" in url:
        return "file"
    elif "/#F!" in url:
        return "folder"
    return "file"

def is_magnet(url):
    magnet = re_match(MAGNET_REGEX, url)
    return bool(magnet)

def get_content_type(link):
    try:
        res = rhead(link, allow_redirects=True, timeout=5, headers = {'user-agent': 'Wget/1.12'})
        content_type = res.headers.get('content-type')
    except:
        try:
            res = urlopen(link, timeout=5)
            info = res.info()
            content_type = info.get_content_type()
        except:
            content_type = None
    return content_type

def is_share_link(url):
    return bool(re_match(r'https?:\/\/.+\.gdtot\.\S+|https?:\/\/(filepress|filebee|appdrive|gdflix)\.\S+', url))

async def add_index_link(name, type, buttons):
    if GD_INDEX_URL:= config_dict['GD_INDEX_URL']:
        url_path = rutils.quote(f'{name}')
        share_url = f'{GD_INDEX_URL}/{url_path}/' if type == "Folder" else f'{GD_INDEX_URL}/{url_path}'
        buttons.url_buildbutton("⚡ Index Link", share_url)
        if config_dict['VIEW_LINK']:
            share_urls = f'{GD_INDEX_URL}/{url_path}?a=view'
            buttons.url_buildbutton("🌐 View Link", share_urls) 

def get_readable_time(seconds):
    result = ''
    (days, remainder) = divmod(seconds, 86400)
    days = int(days)
    if days != 0:
        result += f'{days}d'
    (hours, remainder) = divmod(remainder, 3600)
    hours = int(hours)
    if hours != 0:
        result += f'{hours}h'
    (minutes, seconds) = divmod(remainder, 60)
    minutes = int(minutes)
    if minutes != 0:
        result += f'{minutes}m'
    seconds = int(seconds)
    result += f'{seconds}s'
    return result

def new_thread(fn):
    """To use as decorator to make a function call threaded.
    Needs import
    from threading import Thread"""

    def wrapper(*args, **kwargs):
        thread = Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread

    return wrapper

async def get_readable_message():
    msg = ""
    button= None
    if STATUS_LIMIT := config_dict['STATUS_LIMIT']:
        tasks = len(status_dict)
        globals()['PAGES'] = ceil(tasks/STATUS_LIMIT)
        if PAGE_NO > PAGES and PAGES != 0:
            globals()['COUNT'] -= STATUS_LIMIT
            globals()['PAGE_NO'] -= 1
    for index, download in enumerate(list(status_dict.values())[COUNT:], start=1):
        msg += f"<b>{download.status()}: </b>"
        if download.type() == TaskType.RCLONE:
            msg += f"\n<code>{str(download.name()).upper()}</code>"
        else:
            msg += f"\n<b>Name: </b><code>{escape(str(download.name()))}</code>"
        if download.status() not in [MirrorStatus.STATUS_SPLITTING, MirrorStatus.STATUS_SEEDING]:
            if download.type() == TaskType.RCLONE or download.type() == TaskType.RCLONE_SYNC:
                msg += f"\n{get_progress_bar_rclone(download.progress())} {download.progress()}%"
                msg += f"\n<b>Processed:</b> {download.processed_bytes()}"
            else:
                msg += f"\n{get_progress_bar_string(download)} {download.progress()}"
                if m_queue.qsize() > 0:
                    msg += f"\n<b>Enqueue:</b> {m_queue.qsize()}"
                msg += f"\n<b>Processed:</b> {get_readable_file_size(download.processed_bytes())} of {download.size()}"
            msg += f"\n<b>Speed:</b> {download.speed()} | <b>ETA:</b> {download.eta()}"
            if hasattr(download, 'seeders_num'):
                try:
                    msg += f"\n<b>Seeders:</b> {download.seeders_num()} | <b>Leechers:</b> {download.leechers_num()}"
                except:
                    pass
        else:
            msg += f"\n<b>Size: </b>{download.size()}"
        msg += f"\n<code>/{BotCommands.CancelCommand} {download.gid()}</code>\n\n"
        if index == STATUS_LIMIT:
            break
    if len(msg) == 0:
        return None, None
    dl_speed = 0
    up_speed = 0
    for download in list(status_dict.values()):
        if download.status() == MirrorStatus.STATUS_DOWNLOADING:
            spd = download.speed()
            if 'K' in spd:
                dl_speed += float(spd.split('K')[0]) * 1024
            elif 'M' in spd:
                dl_speed += float(spd.split('M')[0]) * 1048576
        elif download.status() == MirrorStatus.STATUS_UPLOADING:
            spd = download.speed()
            if 'KB/s' in spd:
                up_speed += float(spd.split('K')[0]) * 1024
            elif 'MB/s' in spd:
                up_speed += float(spd.split('M')[0]) * 1048576
        elif download.status() == MirrorStatus.STATUS_SEEDING:
            spd = download.upload_speed()
            if 'K' in spd:
                up_speed += float(spd.split('K')[0]) * 1024
            elif 'M' in spd:
                up_speed += float(spd.split('M')[0]) * 1048576
    if STATUS_LIMIT and tasks > STATUS_LIMIT:
        msg += f"<b>Page:</b> {PAGE_NO}/{PAGES} | <b>Tasks:</b> {tasks}\n"
        buttons = ButtonMaker()
        buttons.cb_buildbutton("⏪", "status pre")
        buttons.cb_buildbutton("⏩", "status nex")
        buttons.cb_buildbutton("♻️", "status ref")
        button = buttons.build_menu(3)
    msg += f"<b>CPU:</b> {cpu_percent()}% | <b>FREE:</b> {get_readable_file_size(disk_usage(DOWNLOAD_DIR).free)}"
    msg += f"\n<b>RAM:</b> {virtual_memory().percent}% | <b>UPTIME:</b> {get_readable_time(time() - botUptime)}"
    msg += f"\n<b>DL:</b> {get_readable_file_size(dl_speed)}/s | <b>UL:</b> {get_readable_file_size(up_speed)}/s"
    return msg, button

async def turn(data):
    STATUS_LIMIT = config_dict['STATUS_LIMIT']
    try:
        global COUNT, PAGE_NO
        async with status_dict_lock:
            if data[1] == "nex":
                if PAGE_NO == PAGES:
                    COUNT = 0
                    PAGE_NO = 1
                else:
                    COUNT += STATUS_LIMIT
                    PAGE_NO += 1
            elif data[1] == "pre":
                if PAGE_NO == 1:
                    COUNT = STATUS_LIMIT * (PAGES - 1)
                    PAGE_NO = PAGES
                else:
                    COUNT -= STATUS_LIMIT
                    PAGE_NO -= 1
        return True
    except:
        return False

class setInterval:
    def __init__(self, interval, action):
        self.interval = interval
        self.action = action
        self.is_cancelled= False
        self.loop= get_running_loop()
        self.loop.create_task(self.setInterval())

    async def setInterval(self):
        nextTime = time() + self.interval
        while True:
            await sleep(nextTime - time())
            nextTime = time() + self.interval
            await self.action()
            if self.is_cancelled:
                break

    def cancel(self):
        self.is_cancelled= True

async def run_sync(func, *args, wait=True, **kwargs):
    pfunc = partial(func, *args, **kwargs)
    with ThreadPoolExecutor() as pool:
        future = botloop.run_in_executor(pool, pfunc)
        if wait:
            return await future 
        else:
            return future

def run_async(func, *args, wait=True, **kwargs):
    future = run_coroutine_threadsafe(func(*args, **kwargs), botloop)
    if wait:
        return future.result()
    else:
        return future

def run_async_task(func, *args, **kwargs):
    return botloop.create_task(func(*args, **kwargs))

async def cmd_exec(cmd, shell=False):
    if shell:
        proc = await create_subprocess_shell(cmd, stdout=PIPE, stderr=PIPE)
    else:
        proc = await create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = await proc.communicate()
    stdout = stdout.decode().strip()
    stderr = stderr.decode().strip()
    return stdout, stderr, proc.returncode

def run_thread_dec(func):
    @wraps(func)
    def wrapper(*args, wait=False, **kwargs):
        future = run_coroutine_threadsafe(func(*args, **kwargs), botloop)
        if wait:
            return future.result()
        else:
            return future
    return wrapper

def command_process(cmd):
    return compile(cmd, IGNORECASE)

def update_user_ldata(id_, key, value):
    if id_ in user_data:
        user_data[id_][key] = value
    else:
        user_data[id_] = {key: value}
