from psutil import cpu_percent, virtual_memory
from bot import uptime
import shutil
import time
from bot.utils.bot_utils import human_format

def get_bottom_status():
     diff = time.time() - uptime
     diff = human_format.human_readable_timedelta(diff)
     usage = shutil.disk_usage("/")
     free = human_format.human_readable_bytes(usage.free) 
     msg= f"\n**CPU:** {cpu_percent()}% | **FREE:** {free}"
     msg += f"\n**RAM:** {virtual_memory().percent}% | **UPTIME:** {diff}"
     return msg 
            