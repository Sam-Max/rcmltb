# Source: https://github.com/anasty17/mirror-leech-telegram-bot/blob/master/generate_drive_token.py
# Adapted for asyncio framework and pyrogram library

from asyncio import sleep, get_running_loop
from html import escape
from math import ceil
from re import findall as re_findall, IGNORECASE, compile
from time import time
from psutil import cpu_percent, disk_usage, virtual_memory
from bot import DOWNLOAD_DIR, status_dict_lock, status_dict, botUptime, config_dict, user_data, m_queue
from requests import head as rhead
from threading import Event, Thread
from urllib.request import urlopen
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.human_format import get_readable_file_size
from bot.helper.ext_utils.misc_utils import ButtonMaker
from bot.helper.mirror_leech_utils.status_utils.status_utils import MirrorStatus, TaskType, get_progress_bar_rclone, get_progress_bar_string


MAGNET_REGEX = r"magnet:\?xt=urn:btih:[a-zA-Z0-9]*"
URL_REGEX = r"(?:(?:https?|ftp):\/\/)?[\w/\-?=%.]+\.[\w/\-?=%.]+"
SIZE_UNITS = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']

COUNT = 0
PAGE_NO = 1
PAGES = 0

def is_url(url: str):
    url = re_findall(URL_REGEX, url)
    return bool(url)

def is_gdrive_link(url: str):
    return "drive.google.com" in url

def is_mega_link(url: str):
    return "mega.nz" in url or "mega.co.nz" in url

def get_mega_link_type(url: str):
    if "folder" in url:
        return "folder"
    elif "file" in url:
        return "file"
    elif "/#F!" in url:
        return "folder"
    return "file"

def is_magnet(url: str):
    magnet = re_findall(MAGNET_REGEX, url)
    return bool(magnet)

def get_content_type(link: str) -> str:
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

def get_readable_time(seconds: int) -> str:
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
    async with status_dict_lock:
        msg = ""
        if STATUS_LIMIT := config_dict['STATUS_LIMIT']:
            tasks = len(status_dict)
            globals()['PAGES'] = ceil(tasks/STATUS_LIMIT)
            if PAGE_NO > PAGES and PAGES != 0:
                globals()['COUNT'] -= STATUS_LIMIT
                globals()['PAGE_NO'] -= 1
        for index, download in enumerate(list(status_dict.values())[COUNT:], start=1):
            msg += f"<b>Status: </b> {download.status()}"
            msg += f"\n<b>Name: </b><code>{escape(str(download.name()))}</code>"
            if download.status() not in [MirrorStatus.STATUS_SPLITTING, MirrorStatus.STATUS_SEEDING]:
                if download.type() == TaskType.RCLONE or download.type() == TaskType.RCLONE_SYNC:
                    msg += f"\n{get_progress_bar_rclone(download.progress())} {download.progress()}%"
                    msg += f"\n<b>Processed:</b> {download.processed_bytes()}"
                else:
                    msg += f"\n{get_progress_bar_string(download)} {download.progress()}"
                    msg += f"\n<b>Enqueue:</b> {m_queue.qsize()}"
                    msg += f"\n<b>Processed:</b> {get_readable_file_size(download.processed_bytes())} of {download.size()}"
                msg += f"\n<b>Speed:</b> {download.speed()} | <b>ETA:</b> {download.eta()}"
                if hasattr(download, 'seeders_num'):
                    try:
                        msg += f"\n<b>Seeders:</b> {download.seeders_num()} | <b>Leechers:</b> {download.leechers_num()}"
                    except:
                        pass
            elif download.status() == MirrorStatus.STATUS_SEEDING:
                msg += f"\n<b>Size: </b>{download.size()}"
                msg += f"\n<b>Speed: </b>{download.upload_speed()}"
                msg += f" | <b>Uploaded: </b>{download.uploaded_bytes()}"
                msg += f"\n<b>Ratio: </b>{download.ratio()}"
                msg += f" | <b>Time: </b>{download.seeding_time()}"
            else:
                msg += f"\n<b>Size: </b>{download.size()}"
            msg += f"\n<code>/{BotCommands.CancelCommand} {download.gid()}</code>"
            msg += "\n\n"
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
        bmsg = f"<b>CPU:</b> {cpu_percent()}% | <b>FREE:</b> {get_readable_file_size(disk_usage(DOWNLOAD_DIR).free)}"
        bmsg += f"\n<b>RAM:</b> {virtual_memory().percent}% | <b>UPTIME:</b> {get_readable_time(time() - botUptime)}"
        bmsg += f"\n<b>DL:</b> {get_readable_file_size(dl_speed)}/s | <b>UL:</b> {get_readable_file_size(up_speed)}/s"
        if STATUS_LIMIT and tasks > STATUS_LIMIT:
            msg += f"<b>Page:</b> {PAGE_NO}/{PAGES} | <b>Tasks:</b> {tasks}\n"
            buttons = ButtonMaker()
            buttons.cb_buildbutton("⏪", "status pre")
            buttons.cb_buildbutton("⏩", "status nex")
            buttons.cb_buildbutton("♻️", "status ref")
            button = buttons.build_menu(3)
            return msg + bmsg, button
        return msg + bmsg, ""

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
            nextTime += self.interval
            await self.action()
            if self.is_cancelled:
                break

    def cancel(self):
        self.is_cancelled= True

class setIntervalThreaded:
    def __init__(self, interval, action):
        self.interval = interval
        self.action = action
        self.stopEvent = Event()
        thread = Thread(target=self.__setInterval)
        thread.start()

    def __setInterval(self):
        nextTime = time() + self.interval
        while not self.stopEvent.wait(nextTime - time()):
            self.action()
            nextTime = time() + self.interval

    def cancel(self):
        self.stopEvent.set()

def command_process(cmd):
    return compile(cmd, IGNORECASE)

def update_user_ldata(id_, key, value):
    if id_ in user_data:
        user_data[id_][key] = value
    else:
        user_data[id_] = {key: value}
