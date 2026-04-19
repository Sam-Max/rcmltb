from asyncio import (
    create_subprocess_exec,
    create_subprocess_shell,
    iscoroutine,
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
    bot_loop,
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
from bot.modules.queue import queue


THREADPOOL = ThreadPoolExecutor(max_workers=1000)
MAGNET_REGEX = r"magnet:\?xt=urn:(btih|btmh):[a-zA-Z0-9]*\s*"
HASH_REGEX = r"urn:btih:([A-Fa-f0-9]{40})"
URL_REGEX = r"^(?!\/)(rtmps?:\/\/|mms:\/\/|rtsp:\/\/|https?:\/\/|ftp:\/\/)?([^\/:]+:[^\/@]+@)?(www\.)?(?=[^\/:\s]+\.[^\/:\s]+)([^\/:\s]+\.[^\/:\s]+)(:\d+)?(\/[^#\s]*[\s\S]*)?(\?[^#\s]*)?(#.*)?$"
SIZE_UNITS = ["B", "KB", "MB", "GB", "TB", "PB"]

PAGES = 1

# Per-chat status pagination state
# {chat_id: {"start": 0, "page": 1, "filter": "all"}}
status_pages = {}

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

# Link validation functions moved to links_utils.py (backward compat imports)
from bot.helper.ext_utils.links_utils import (
    is_url,
    is_gdrive_link,
    is_gdrive_id,
    is_mega_link,
    is_magnet,
    is_share_link,
    is_telegram_link,
    is_rclone_path,
)


def get_mega_link_type(url):
    if "folder" in url:
        return "folder"
    elif "/#F!" in url:
        return "folder"
    else:
        return "file"


async def get_content_type(link):
    try:
        async with ClientSession(trust_env=True) as session:
            async with session.get(link, verify_ssl=False) as response:
                return response.headers.get("Content-Type")
    except Exception:
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


def get_size_bytes(size_text):
    """Convert size string like '2.5 GB', '1.2 GiB' to bytes."""
    if not size_text:
        return 0
    size_text = size_text.strip().lower()
    if not size_text:
        return 0
    try:
        # Extract number and unit
        import re
        match = re.match(r"(\d+(?:\.\d+)?)\s*(b|kb|mb|gb|tb|pb|kib|mib|gib|tib|pib)?", size_text)
        if not match:
            return 0
        number = float(match.group(1))
        unit = match.group(2) or "b"
        units = {
            "b": 1,
            "kb": 1024,
            "mb": 1024 ** 2,
            "gb": 1024 ** 3,
            "tb": 1024 ** 4,
            "pb": 1024 ** 5,
            "kib": 1024,
            "mib": 1024 ** 2,
            "gib": 1024 ** 3,
            "tib": 1024 ** 4,
            "pib": 1024 ** 5,
        }
        return int(number * units.get(unit, 1))
    except Exception:
        return 0


def get_readable_message(chat_id=None, status_filter="all"):
    msg = ""
    button = None
    STATUS_LIMIT = config_dict["STATUS_LIMIT"]

    # Get per-chat state or use defaults
    if chat_id and chat_id in status_pages:
        start = status_pages[chat_id]["start"]
        page = status_pages[chat_id]["page"]
    else:
        start = 0
        page = 1

    # Filter tasks based on status_filter
    all_tasks = list(status_dict.values())
    if status_filter != "all":
        filter_map = {
            "dl": [MirrorStatus.STATUS_DOWNLOADING, MirrorStatus.STATUS_QUEUEDL],
            "ul": [MirrorStatus.STATUS_UPLOADING, MirrorStatus.STATUS_QUEUEUP],
            "seed": [MirrorStatus.STATUS_SEEDING],
            "clone": [MirrorStatus.STATUS_CLONING],
            "queue": [MirrorStatus.STATUS_QUEUEDL, MirrorStatus.STATUS_QUEUEUP],
        }
        if status_filter in filter_map:
            all_tasks = [t for t in all_tasks if t.status() in filter_map[status_filter]]

    tasks = len(all_tasks)
    globals()["PAGES"] = (tasks + STATUS_LIMIT - 1) // STATUS_LIMIT if tasks > 0 else 1

    # Adjust page if out of bounds
    if page > PAGES and PAGES != 0:
        page = PAGES
        start = STATUS_LIMIT * (PAGES - 1)
        if chat_id:
            status_pages[chat_id] = {"start": start, "page": page, "filter": status_filter}

    for download in all_tasks[start : STATUS_LIMIT + start]:
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
                msg += f"\n<b>Processed:</b> {download.processed_bytes()} of {download.size()}"
            if queue:
                msg += f"\n<b>Enqueue:</b> {queue.queue.qsize()}/{queue.queue.maxsize}"
            msg += f"\n<b>Speed:</b> {download.speed()} | <b>ETA:</b> {download.eta()}"
            if hasattr(download, "seeders_num"):
                try:
                    msg += f"\n<b>Seeders:</b> {download.seeders_num()} | <b>Leechers:</b> {download.leechers_num()}"
                except Exception:
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
            dl_speed += text_size_to_bytes(download.speed())
        elif tstatus == MirrorStatus.STATUS_UPLOADING:
            up_speed += text_size_to_bytes(download.speed())
        elif tstatus == MirrorStatus.STATUS_SEEDING:
            up_speed += text_size_to_bytes(download.upload_speed())

    # Build buttons
    buttons = ButtonMaker()

    # Add filter buttons
    filter_labels = {
        "all": "All",
        "dl": "DL",
        "ul": "UL",
        "seed": "Seed",
        "clone": "Clone",
        "queue": "Queue",
    }
    for filter_key, filter_label in filter_labels.items():
        prefix = "✓" if status_filter == filter_key else ""
        buttons.cb_buildbutton(f"{prefix}{filter_label}", f"status filter {filter_key}")

    # Add navigation buttons
    if tasks > STATUS_LIMIT or PAGES > 1:
        buttons.cb_buildbutton("⏪", "status pre")
        buttons.cb_buildbutton(f"{page}/{PAGES}", "status stats")
        buttons.cb_buildbutton("⏩", "status nex")

    # Add step buttons for direct page navigation
    if PAGES > 1:
        for i in range(1, min(PAGES + 1, 6)):  # Show up to 5 page buttons
            buttons.cb_buildbutton(str(i), f"status step {i}")

    buttons.cb_buildbutton("♻️", "status ref")
    button = buttons.build_menu(3)

    msg += f"<b>CPU:</b> {cpu_percent()}% | <b>FREE:</b> {get_readable_file_size(disk_usage(config_dict['DOWNLOAD_DIR']).free)}"
    msg += f"\n<b>RAM:</b> {virtual_memory().percent}% | <b>UPTIME:</b> {get_readable_time(time() - botUptime)}"
    msg += f"\n<b>DL:</b> {get_readable_file_size(dl_speed)}/s | <b>UL:</b> {get_readable_file_size(up_speed)}/s"
    return msg, button


def text_size_to_bytes(size_text):
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
    return size


async def turn(data, chat_id=None):
    STATUS_LIMIT = config_dict["STATUS_LIMIT"]

    # Get current state
    if chat_id and chat_id in status_pages:
        start = status_pages[chat_id]["start"]
        page = status_pages[chat_id]["page"]
        current_filter = status_pages[chat_id].get("filter", "all")
    else:
        start = 0
        page = 1
        current_filter = "all"

    async with status_dict_lock:
        if data[1] == "nex":
            if page == PAGES:
                start = 0
                page = 1
            else:
                start += STATUS_LIMIT
                page += 1
        elif data[1] == "pre":
            if page == 1:
                start = STATUS_LIMIT * (PAGES - 1)
                page = PAGES
            else:
                start -= STATUS_LIMIT
                page -= 1
        elif data[1] == "filter" and len(data) > 2:
            # Handle filter button
            current_filter = data[2]
            start = 0
            page = 1
        elif data[1] == "step" and len(data) > 2:
            # Handle step button (direct page navigation)
            try:
                target_page = int(data[2])
                if 1 <= target_page <= PAGES:
                    page = target_page
                    start = STATUS_LIMIT * (page - 1)
            except ValueError:
                pass

    # Save updated state
    if chat_id:
        status_pages[chat_id] = {"start": start, "page": page, "filter": current_filter}

    return current_filter


class setInterval:
    def __init__(self, interval, action):
        self.interval = interval
        self.action = action
        self.task = bot_loop.create_task(self.setInterval())

    async def setInterval(self):
        while True:
            await sleep(self.interval)
            await self.action()

    def cancel(self):
        self.task.cancel()


async def run_sync_to_async(func, *args, wait=True, **kwargs):
    pfunc = partial(func, *args, **kwargs)
    future = bot_loop.run_in_executor(THREADPOOL, pfunc)
    if wait:
        return await future
    else:
        return future


def run_async_to_sync(func, *args, wait=True, **kwargs):
    coro = func if iscoroutine(func) else func(*args, **kwargs)
    future = run_coroutine_threadsafe(coro, bot_loop)
    if wait:
        return future.result()
    else:
        return future


def create_task(func, *args, **kwargs):
    return bot_loop.create_task(func(*args, **kwargs))


def new_task(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return bot_loop.create_task(func(*args, **kwargs))

    return wrapper


def new_thread(func):
    @wraps(func)
    def wrapper(*args, wait=False, **kwargs):
        future = run_coroutine_threadsafe(func(*args, **kwargs), bot_loop)
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
        future = run_coroutine_threadsafe(func(*args, **kwargs), bot_loop)
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
    for dirpath, _, files in await run_sync_to_async(walk, path, topdown=False):
        for filee in files:
            if (
                filee.endswith(".!qB")
                or filee.endswith(".parts")
                and filee.startswith(".")
            ):
                osremove(ospath.join(dirpath, filee))
        if dirpath.endswith((".unwanted")):
            rmtree(dirpath)
    for dirpath, _, files in await run_sync_to_async(walk, path, topdown=False):
        if not listdir(dirpath):
            rmdir(dirpath)
