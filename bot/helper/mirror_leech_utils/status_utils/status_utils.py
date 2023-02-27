
import time
from math import floor
from functools import partial
from os import listdir, rmdir, walk, path as ospath, remove
from psutil import cpu_percent, virtual_memory
from bot import LOGGER, botUptime, botloop
from shutil import disk_usage, rmtree
from bot.helper.ext_utils.human_format import human_readable_bytes, human_readable_timedelta

def get_bottom_status():
     diff = time.time() - botUptime
     diff = human_readable_timedelta(diff)
     usage = disk_usage("/")
     free = human_readable_bytes(usage.free) 
     msg= f"\n**CPU:** {cpu_percent()}% | **FREE:** {free}"
     msg += f"\n**RAM:** {virtual_memory().percent}% | **UPTIME:** {diff}"
     return msg 

class MirrorStatus:
    STATUS_UPLOADING = "Uploading"
    STATUS_CLONING= "Cloning"
    STATUS_DOWNLOADING = "Downloading"
    STATUS_COPYING= "Copying"
    STATUS_SYNCING= "Syncing"
    STATUS_ARCHIVING = "Archiving 🔐"
    STATUS_EXTRACTING = "Extracting 📂"
    STATUS_SPLITTING = "Splitting ✂️"
    STATUS_WAITING = "Queue"
    STATUS_PAUSED = "Pause"
    STATUS_CHECKING = "CheckUp"
    STATUS_SEEDING = "Seed"

class TaskType():
    RCLONE= "Rclone"
    RCLONE_SYNC= "RcloneSync"
    TELEGRAM= "Telegram"

def get_progress_bar_string(status):
    completed = status.processed_bytes() / 8
    total = status.size_raw() / 8
    p = 0 if total == 0 else round(completed * 100 / total)
    p = min(max(p, 0), 100)
    cFull = p // 8
    p_str = '■' * cFull
    p_str += '□' * (12 - cFull)
    p_str = f"[{p_str}]"
    return p_str

def get_progress_bar_rclone(percentage):
    return "{0}{1}".format(
    ''.join(['■' for i in range(floor(percentage / 10))]),
    ''.join(['□' for i in range(10 - floor(percentage / 10))]))

async def clean_unwanted(path: str):
    LOGGER.info(f"Cleaning unwanted files/folders: {path}")
    for dirpath, subdir, files in await botloop.run_in_executor(None, partial(walk, path, topdown=False)):
        for filee in files:
            if filee.endswith(".!qB") or filee.endswith('.parts') and filee.startswith('.'):
                remove(ospath.join(dirpath, filee))
        if dirpath.endswith((".unwanted", "splited_files")):
            rmtree(dirpath)
    for dirpath, subdir, files in await botloop.run_in_executor(None, partial(walk, path, topdown=False)):
        if not listdir(dirpath):
            rmdir(dirpath)