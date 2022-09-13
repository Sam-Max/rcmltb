from os import listdir, rmdir, walk, path as ospath, remove
import time
from psutil import cpu_percent, virtual_memory
from bot import LOGGER, botUptime
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
    STATUS_UPLOADING = "Uploading..."
    STATUS_CLONING= "Cloning..."
    STATUS_DOWNLOADING = "Downloading..."
    STATUS_COPYING= "Copying..."
    STATUS_ARCHIVING = "Archiving...🔐"
    STATUS_EXTRACTING = "Extracting...📂"
    STATUS_SPLITTING = "Splitting...✂️"
    STATUS_WAITING = "Queue"
    STATUS_PAUSED = "Pause"
    STATUS_CHECKING = "CheckUp"

def clean_unwanted(path: str):
    LOGGER.info(f"Cleaning unwanted files/folders: {path}")
    for dirpath, subdir, files in walk(path, topdown=False):
        for filee in files:
            if filee.endswith(".!qB") or filee.endswith('.parts') and filee.startswith('.'):
                remove(ospath.join(dirpath, filee))
        if dirpath.endswith((".unwanted", "splited_files_mltb")):
            rmtree(dirpath)
    for dirpath, subdir, files in walk(path, topdown=False):
        if not listdir(dirpath):
            rmdir(dirpath)