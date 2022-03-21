#Modified from:
#https://github.com/yash-dk/TorToolkit-Telegram/blob/master/tortoolkit/core/HandleManager.py

import shutil
import psutil
from psutil import net_io_counters
from telethon.tl.types import KeyboardButtonCallback
from telethon import events
import time
from bot.core.get_vars import get_val
from ... import uptime
from bot.utils import human_format


async def handle_server_command(e):
        user_id= e.sender_id
        chat_id= e.chat_id
        if user_id in get_val("ALLOWED_USERS") or chat_id in get_val("ALLOWED_CHATS") or user_id == get_val("OWNER_ID"):
            print(type(e))
            if isinstance(e, events.CallbackQuery.Event):
                callbk = True
            else:
                callbk = False

            try:
                mem = psutil.virtual_memory()
                memavailable = human_format.human_readable_bytes(mem.available)
                memtotal = human_format.human_readable_bytes(mem.total)
                mempercent = mem.percent
                memfree = human_format.human_readable_bytes(mem.free)
            except:
                memavailable = "N/A"
                memtotal = "N/A"
                mempercent = "N/A"
                memfree = "N/A"

            try:
                cpufreq = psutil.cpu_freq()
                freqcurrent = cpufreq.current
                freqmax = cpufreq.max
            except:
                freqcurrent = "N/A"
                freqmax = "N/A"

            try:
                cores = psutil.cpu_count(logical=False)
                lcores = psutil.cpu_count()
            except:
                cores = "N/A"
                lcores = "N/A"

            try:
                cpupercent = psutil.cpu_percent()
            except:
                cpupercent = "N/A"

            try:
                usage = shutil.disk_usage("/")
                totaldsk = human_format.human_readable_bytes(usage.total)
                useddsk = human_format.human_readable_bytes(usage.used)
                freedsk = human_format.human_readable_bytes(usage.free)
            except:
                totaldsk = "N/A"
                useddsk = "N/A"
                freedsk = "N/A"

            try:
                recv = human_format.human_readable_bytes(net_io_counters().bytes_recv)
                sent = human_format.human_readable_bytes(net_io_counters().bytes_sent)
            except:
                recv = "N/A"
                sent = "N/A"

            diff = time.time() - uptime
            diff = human_format.human_readable_timedelta(diff)

            if callbk:
                msg = (
                    f"<b>BOT UPTIME:-</b> {diff}\n\n"
                    "<b>CPU STATS:-</b>\n"
                    f"Cores: {cores} Logical: {lcores}\n"
                    f"CPU Frequency: {freqcurrent}  Mhz Max: {freqmax}\n"
                    f"CPU Utilization: {cpupercent}%\n"
                    "\n"
                    "<b>STORAGE STATS:-</b>\n"
                    f"Total: {totaldsk}\n"
                    f"Used: {useddsk}\n"
                    f"Free: {freedsk}\n"
                    "\n"
                    "<b>MEMORY STATS:-</b>\n"
                    f"Available: {memavailable}\n"
                    f"Total: {memtotal}\n"
                    f"Usage: {mempercent}%\n"
                    f"Free: {memfree}\n"
                    "\n"
                    "<b>TRANSFER INFO:</b>\n"
                    f"Download: {recv}\n"
                    f"Upload: {sent}\n"
                )
                await e.edit(msg, parse_mode="html", buttons=None)
            else:
                try:
                    storage_percent = round((usage.used / usage.total) * 100, 2)
                except:
                    storage_percent = 0

                msg = (
                    f"<b>BOT UPTIME:-</b> {diff}\n\n"
                    f"CPU Utilization: {progress_bar(cpupercent)} - {cpupercent}%\n\n"
                    f"Storage used:- {progress_bar(storage_percent)} - {storage_percent}%\n"
                    f"Total: {totaldsk} Free: {freedsk}\n\n"
                    f"Memory used:- {progress_bar(mempercent)} - {mempercent}%\n"
                    f"Total: {memtotal} Free: {memfree}\n\n"
                    f"Download:- {recv}\n"
                    f"Upload:- {sent}\n"
                )
                await e.reply(msg, parse_mode="html",
                                    buttons=[[KeyboardButtonCallback("Get detailed stats.", "fullserver")]])
        else:
            await e.reply('Not Authorized user')  
        

def progress_bar(percentage):
    # percentage is on the scale of 0-1
    comp = "▰"
    ncomp = "▱"
    pr = ""

    if isinstance(percentage, str):
        return "NaN"

    try:
        percentage = int(percentage)
    except:
        percentage = 0

    for i in range(1, 11):
        if i <= int(percentage / 10):
            pr += comp
        else:
            pr += ncomp
    return pr                            