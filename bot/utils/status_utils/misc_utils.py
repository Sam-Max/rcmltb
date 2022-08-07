from psutil import cpu_percent, virtual_memory
from bot import uptime
from shutil import disk_usage
import time
from bot.utils.bot_utils.human_format import human_readable_timedelta, human_readable_bytes

def get_bottom_status():
     diff = time.time() - uptime
     diff = human_readable_timedelta(diff)
     usage = disk_usage("/")
     free = human_readable_bytes(usage.free) 
     msg= f"\n**CPU:** {cpu_percent()}% | **FREE:** {free}"
     msg += f"\n**RAM:** {virtual_memory().percent}% | **UPTIME:** {diff}"
     return msg 

class MirrorStatus:
    STATUS_UPLOADING = "Uploading..."
    STATUS_DOWNLOADING = "Downloading..."
    STATUS_COPYING= "Copying..."
    STATUS_ARCHIVING = "Archiving..."
    STATUS_EXTRACTING = "Extracting..."
    STATUS_SPLITTING = "Splitting..."

def humanbytes(size: int) -> str:
    """ converts bytes into human readable format """
    # https://stackoverflow.com/a/49361727/4723940
    # 2**10 = 1024
    if not size:
        return ""
    power = 2 ** 10
    number = 0
    dict_power_n = {
        0: " ",
        1: "Ki",
        2: "Mi",
        3: "Gi",
        4: "Ti"
    }
    while size > power:
        size /= power
        number += 1
    return str(round(size, 2)) + " " + dict_power_n[number] + 'B'

def time_formatter(milliseconds: int) -> str:
    """ converts seconds into human readable format """
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
          ((str(hours) + "h, ") if hours else "") + \
          ((str(minutes) + "m, ") if minutes else "") + \
          ((str(seconds) + "s, ") if seconds else "") + \
          ((str(milliseconds) + "ms, ") if milliseconds else "")
    return tmp[:-2]
            