from asyncio import (
    create_subprocess_exec,
    create_subprocess_shell,
    run_coroutine_threadsafe,
    sleep,
)
from asyncio.subprocess import PIPE
from concurrent.futures import ThreadPoolExecutor
from functools import partial, wraps
from html import escape
from time import time
from os import walk, path as ospath, remove as osremove, rmdir, listdir
from shutil import rmtree
from re import IGNORECASE, compile, match as re_match, search
from aiohttp import ClientSession
from psutil import cpu_percent, disk_usage, virtual_memory
from bot import (
    LOGGER,
    status_dict_lock,
    status_dict,
    botUptime,
    config_dict,
    user_data,
    m_queue,
    botloop,
)
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.human_format import get_readable_file_size
from bot.helper.mirror_leech_utils.status_utils.status_utils import (
    MirrorStatus,
    TaskType,
    get_progress_bar_rclone,
    get_progress_bar_string,
)


THREADPOOL = ThreadPoolExecutor(max_workers=1000)
MAGNET_REGEX = r"magnet:\?xt=urn:(btih|btmh):[a-zA-Z0-9]*\s*"
URL_REGEX = r"^(?!\/)(rtmps?:\/\/|mms:\/\/|rtsp:\/\/|https?:\/\/|ftp:\/\/)?([^\/:]+:[^\/@]+@)?(www\.)?(?=[^\/:\s]+\.[^\/:\s]+)([^\/:\s]+\.[^\/:\s]+)(:\d+)?(\/[^#\s]*[\s\S]*)?(\?[^#\s]*)?(#.*)?$"
SIZE_UNITS = ["B", "KB", "MB", "GB", "TB", "PB"]

STATUS_START = 0
PAGE_NO = 1
PAGES = 1

ARCH_EXT = [
    ".tar.bz2",
    ".tar.gz",
    ".bz2",
    ".gz",
    ".tar.xz",
    ".tar",
    ".tbz2",
    ".tgz",
    ".lzma2",
    ".zip",
    ".7z",
    ".z",
    ".rar",
    ".iso",
    ".wim",
    ".cab",
    ".apm",
    ".arj",
    ".chm",
    ".cpio",
    ".cramfs",
    ".deb",
    ".dmg",
    ".fat",
    ".hfs",
    ".lzh",
    ".lzma",
    ".mbr",
    ".msi",
    ".mslz",
    ".nsis",
    ".ntfs",
    ".rpm",
    ".squashfs",
    ".udf",
    ".vhd",
    ".xar",
]

FIRST_SPLIT_REGEX = r"(\.|_)part0*1\.rar$|(\.|_)7z\.0*1$|(\.|_)zip\.0*1$|^(?!.*(\.|_)part\d+\.rar$).*\.rar$"

SPLIT_REGEX = r"\.r\d+$|\.7z\.\d+$|\.z\d+$|\.zip\.\d+$"


def is_first_archive_split(file):
    return bool(search(FIRST_SPLIT_REGEX, file))


def is_archive(file):
    return file.endswith(tuple(ARCH_EXT))


def is_archive_split(file):
    return bool(search(SPLIT_REGEX, file))


def is_url(url):
    return bool(re_match(URL_REGEX, url))


def is_gdrive_link(url):
    return "drive.google.com" in url


def is_mega_link(url):
    return "mega.nz" in url or "mega.co.nz" in url


def get_mega_link_type(url):
    if "folder" in url:
        return "folder"
    elif "/#F!" in url:
        return "folder"
    else:
        return "file"


def is_magnet(url):
    return bool(re_match(MAGNET_REGEX, url))


async def get_content_type(link):
    try:
        async with ClientSession(trust_env=True) as session:
            async with session.get(link, verify_ssl=False) as response:
                return response.headers.get("Content-Type")
    except:
        return None


def is_share_link(url):
    return bool(
        re_match(
            r"https?:\/\/.+\.gdtot\.\S+|https?:\/\/(filepress|filebee|appdrive|gdflix)\.\S+",
            url,
        )
    )


def get_readable_time(seconds):
    result = ""
    (days, remainder) = divmod(seconds, 86400)
    days = int(days)
    if days != 0:
        result += f"{days}d"
    (hours, remainder) = divmod(remainder, 3600)
    hours = int(hours)
    if hours != 0:
        result += f"{hours}h"
    (minutes, seconds) = divmod(remainder, 60)
    minutes = int(minutes)
    if minutes != 0:
        result += f"{minutes}m"
    seconds = int(seconds)
    result += f"{seconds}s"
    return result


def speed_string_to_bytes(size_text: str):
    size = 0
    size_text = size_text.lower()
    if "k" in size_text:
        size += float(size_text.split("k")[0]) * 1024
    elif "m" in size_text:
        size += float(size_text.split("m")[0]) * 1048576
    elif "g" in size_text:
        size += float(size_text.split("g")[0]) * 1073741824
    elif "t" in size_text:
        size += float(size_text.split("t")[0]) * 1099511627776
    elif "b" in size_text:
        size += float(size_text.split("b")[0])
    return size


def get_readable_message():
    msg = ""
    button = None
    STATUS_LIMIT = config_dict["STATUS_LIMIT"]
    tasks = len(status_dict)
    globals()["PAGES"] = (tasks + STATUS_LIMIT - 1) // STATUS_LIMIT
    if PAGE_NO > PAGES and PAGES != 0:
        globals()["STATUS_START"] = STATUS_LIMIT * (PAGES - 1)
        globals()["PAGE_NO"] = PAGES
    for download in list(status_dict.values())[
        STATUS_START : STATUS_LIMIT + STATUS_START
    ]:
        if download.message.chat.type.name in ["SUPERGROUP", "CHANNEL"]:
            msg += f"<b><a href='{download.message.link}'>{download.status()}</a>: </b>"
        else:
            msg += f"<b>{download.status()}: </b>"
        if download.type() == TaskType.RCLONE:
            msg += f"\n<code>{str(download.name())}</code>"
        else:
            msg += f"<code>{escape(f'{download.name()}')}</code>"
        if download.status() not in [
            MirrorStatus.STATUS_SPLITTING,
            MirrorStatus.STATUS_SEEDING,
        ]:
            if (
                download.type() == TaskType.RCLONE
                or download.type() == TaskType.RCLONE_SYNC
            ):
                msg += f"\n{get_progress_bar_rclone(download.progress())} {download.progress()}%"
                msg += f"\n<b>Processed:</b> {download.processed_bytes()}"
            else:
                msg += f"\n{get_progress_bar_string(download.progress())} {download.progress()}"
                if m_queue.qsize() > 0:
                    msg += f"\n<b>Enqueue:</b> {m_queue.qsize()}"
                msg += f"\n<b>Processed:</b> {download.processed_bytes()} of {download.size()}"
            msg += f"\n<b>Speed:</b> {download.speed()} | <b>ETA:</b> {download.eta()}"
            if hasattr(download, "seeders_num"):
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
        msg += f"\n<code>/{BotCommands.CancelCommand} {download.gid()}</code>\n\n"
    if len(msg) == 0:
        return None, None
    dl_speed = 0
    up_speed = 0
    for download in status_dict.values():
        tstatus = download.status()
        if tstatus == MirrorStatus.STATUS_DOWNLOADING:
            spd = download.speed()
            if "K" in spd:
                dl_speed += float(spd.split("K")[0]) * 1024
            elif "M" in spd:
                dl_speed += float(spd.split("M")[0]) * 1048576
        elif tstatus == MirrorStatus.STATUS_UPLOADING:
            spd = download.speed()
            if "K" in spd:
                up_speed += float(spd.split("K")[0]) * 1024
            elif "M" in spd:
                up_speed += float(spd.split("M")[0]) * 1048576
        elif tstatus == MirrorStatus.STATUS_SEEDING:
            spd = download.upload_speed()
            if "K" in spd:
                up_speed += float(spd.split("K")[0]) * 1024
            elif "M" in spd:
                up_speed += float(spd.split("M")[0]) * 1048576
    if tasks > STATUS_LIMIT:
        msg += f"<b>Page:</b> {PAGE_NO}/{PAGES} | <b>Tasks:</b> {tasks}\n"
        buttons = ButtonMaker()
        buttons.cb_buildbutton("⏪", "status pre")
        buttons.cb_buildbutton("⏩", "status nex")
        buttons.cb_buildbutton("♻️", "status ref")
        button = buttons.build_menu(3)
    msg += f"<b>CPU:</b> {cpu_percent()}% | <b>FREE:</b> {get_readable_file_size(disk_usage(config_dict['DOWNLOAD_DIR']).free)}"
    msg += f"\n<b>RAM:</b> {virtual_memory().percent}% | <b>UPTIME:</b> {get_readable_time(time() - botUptime)}"
    msg += f"\n<b>DL:</b> {get_readable_file_size(dl_speed)}/s | <b>UL:</b> {get_readable_file_size(up_speed)}/s"
    return msg, button


async def turn(data):
    STATUS_LIMIT = config_dict["STATUS_LIMIT"]
    global STATUS_START, PAGE_NO
    async with status_dict_lock:
        if data[1] == "nex":
            if PAGE_NO == PAGES:
                STATUS_START = 0
                PAGE_NO = 1
            else:
                STATUS_START += STATUS_LIMIT
                PAGE_NO += 1
        elif data[1] == "pre":
            if PAGE_NO == 1:
                STATUS_START = STATUS_LIMIT * (PAGES - 1)
                PAGE_NO = PAGES
            else:
                STATUS_START -= STATUS_LIMIT
                PAGE_NO -= 1


class setInterval:
    def __init__(self, interval, action):
        self.interval = interval
        self.action = action
        self.is_cancelled = False
        botloop.create_task(self.setInterval())

    async def setInterval(self):
        while True:
            await sleep(self.interval)
            await self.action()
            if self.is_cancelled:
                break

    def cancel(self):
        self.is_cancelled = True


async def run_sync(func, *args, wait=True, **kwargs):
    pfunc = partial(func, *args, **kwargs)
    future = botloop.run_in_executor(THREADPOOL, pfunc)
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


def create_task(func, *args, **kwargs):
    return botloop.create_task(func(*args, **kwargs))


def new_task(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return botloop.create_task(func(*args, **kwargs))

    return wrapper


def new_thread(func):
    @wraps(func)
    def wrapper(*args, wait=False, **kwargs):
        future = run_coroutine_threadsafe(func(*args, **kwargs), botloop)
        return future.result() if wait else future

    return wrapper


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
    user_data.setdefault(id_, {})
    user_data[id_][key] = value


async def clean_unwanted(path):
    LOGGER.info(f"Cleaning unwanted files/folders: {path}")
    for dirpath, _, files in await run_sync(walk, path, topdown=False):
        for filee in files:
            if (
                filee.endswith(".!qB")
                or filee.endswith(".parts")
                and filee.startswith(".")
            ):
                osremove(ospath.join(dirpath, filee))
        if dirpath.endswith((".unwanted")):
            rmtree(dirpath)
    for dirpath, _, files in await run_sync(walk, path, topdown=False):
        if not listdir(dirpath):
            rmdir(dirpath)
