from psutil import (
    disk_usage,
    cpu_percent,
    swap_memory,
    cpu_count,
    virtual_memory,
    net_io_counters,
    boot_time,
)
from pyrogram.handlers import MessageHandler
from pyrogram.filters import command
from time import time
from os import path as ospath
from bot.helper.telegram_helper.message_utils import sendMessage
from bot import bot, botUptime
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.ext_utils.bot_utils import cmd_exec, get_readable_time
from bot.helper.ext_utils.human_format import get_readable_file_size
from bot.helper.telegram_helper.filters import CustomFilters


async def stats(client, message):
    if ospath.exists(".git"):
        last_commit = await cmd_exec(
            "git log -1 --date=short --pretty=format:'%cd <b>From</b> %cr'", True
        )
        last_commit = last_commit[0]
    else:
        last_commit = "No UPSTREAM_REPO"
    total, used, free, disk = disk_usage("/")
    swap = swap_memory()
    memory = virtual_memory()
    stats = (
        f"📊 <b>Bot Statistics</b>\n\n"
        f"<b>Commit Date:</b> <code>{last_commit}</code>\n"
        f"<b>Bot Uptime:</b> <code>{get_readable_time(time() - botUptime)}</code>\n"
        f"<b>OS Uptime:</b> <code>{get_readable_time(time() - boot_time())}</code>\n\n"
        f"💾 <b>Disk</b>\n"
        f"├ <b>Total:</b> <code>{get_readable_file_size(total)}</code>\n"
        f"├ <b>Used:</b> <code>{get_readable_file_size(used)}</code> | <b>Free:</b> <code>{get_readable_file_size(free)}</code>\n"
        f"└ <b>Usage:</b> <code>{disk}%</code>\n\n"
        f"🌐 <b>Network</b>\n"
        f"├ <b>Upload:</b> <code>{get_readable_file_size(net_io_counters().bytes_sent)}</code>\n"
        f"└ <b>Download:</b> <code>{get_readable_file_size(net_io_counters().bytes_recv)}</code>\n\n"
        f"🖥 <b>System</b>\n"
        f"├ <b>CPU:</b> <code>{cpu_percent(interval=0.5)}%</code>\n"
        f"├ <b>Physical Cores:</b> <code>{cpu_count(logical=False)}</code>\n"
        f"└ <b>Total Cores:</b> <code>{cpu_count(logical=True)}</code>\n\n"
        f"🧠 <b>Memory</b>\n"
        f"├ <b>Total:</b> <code>{get_readable_file_size(memory.total)}</code>\n"
        f"├ <b>Used:</b> <code>{get_readable_file_size(memory.used)}</code> | <b>Free:</b> <code>{get_readable_file_size(memory.available)}</code>\n"
        f"├ <b>Usage:</b> <code>{memory.percent}%</code>\n"
        f"├ <b>SWAP Total:</b> <code>{get_readable_file_size(swap.total)}</code>\n"
        f"└ <b>SWAP Used:</b> <code>{swap.percent}%</code>\n"
    )
    await sendMessage(stats, message)


bot.add_handler(
    MessageHandler(
        stats,
        filters=command(BotCommands.StatsCommand)
        & (CustomFilters.user_filter | CustomFilters.chat_filter),
    )
)
