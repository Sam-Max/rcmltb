from pyrogram.filters import command
from pyrogram.handlers import MessageHandler
from time import time

from bot import LOGGER
from bot.core.telegram_manager import TgClient
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import editMessage, sendMarkup, sendMessage
from bot.helper.ext_utils.bot_utils import cmd_exec
from bot.helper.ext_utils.misc_utils import clean_all, exit_clean_up, start_cleanup
from asyncio import create_subprocess_exec
from aiofiles import open as aiopen
from os import path as ospath, remove as osremove, execl as osexecl
from sys import executable
from signal import signal, SIGINT


async def start(_, message):
    from bot.helper.telegram_helper.button_build import ButtonMaker

    buttons = ButtonMaker()
    buttons.url_buildbutton("Repo", "https://github.com/Sam-Max/rcmltb")
    buttons.url_buildbutton("Owner", "https://github.com/Sam-Max")
    reply_markup = buttons.build_menu(2)
    if CustomFilters.user_filter or CustomFilters.chat_filter:
        msg = (
            "**Hello, Welcome to Rclone-Telegram-Bot!\n\n"
            "I can help you copy files from one cloud to another.\n"
            "I can also mirror-leech files and links to Telegram or cloud**\n\n"
        )
        await sendMarkup(msg, message, reply_markup)
    else:
        await sendMarkup(
            "Not Authorized user, deploy your own version", message, reply_markup
        )


async def restart(_, message):
    from bot import scheduler, Interval

    restart_msg = await sendMessage("Restarting...", message)
    if scheduler.running:
        scheduler.shutdown(wait=False)
    if Interval:
        for intvl in list(Interval.values()):
            intvl.cancel()
    await clean_all()
    await (
        await create_subprocess_exec(
            "pkill", "-9", "-f", "gunicorn|aria2c|rclone|qbittorrent-nox|ffmpeg"
        )
    ).wait()
    await (await create_subprocess_exec("python3", "update.py")).wait()
    async with aiopen(".restartmsg", "w") as f:
        await f.write(f"{restart_msg.chat.id}\n{restart_msg.id}\n")
    osexecl(executable, executable, "-m", "bot")


async def ping(_, message):
    start_time = int(round(time() * 1000))
    reply = await sendMessage("Starting Ping", message)
    end_time = int(round(time() * 1000))
    await editMessage(f"{end_time - start_time} ms", reply)


async def get_ip(_, message):
    stdout, stderr, code = await cmd_exec("curl https://api.ipify.org/", shell=True)
    if code == 0:
        await message.reply_text(f"Your IP is {stdout.strip()}")
    else:
        await message.reply_text(f"Error: {stderr}")


async def get_log(client, message):
    await client.send_document(chat_id=message.chat.id, document="botlog.txt")


def add_handlers():
    """Register all bot handlers centrally."""
    bot = TgClient.bot

    # Core handlers (from __main__.py)
    bot.add_handler(
        MessageHandler(start, filters=command(BotCommands.StartCommand))
    )
    bot.add_handler(
        MessageHandler(
            restart,
            filters=command(BotCommands.RestartCommand)
            & (CustomFilters.owner_filter | CustomFilters.sudo_filter),
        )
    )
    bot.add_handler(
        MessageHandler(
            get_log,
            filters=command(BotCommands.LogsCommand)
            & (CustomFilters.owner_filter | CustomFilters.sudo_filter),
        )
    )
    bot.add_handler(
        MessageHandler(
            ping,
            filters=command(BotCommands.PingCommand)
            & (CustomFilters.user_filter | CustomFilters.chat_filter),
        )
    )
    bot.add_handler(
        MessageHandler(get_ip, filters=command(BotCommands.IpCommand))
    )

    # Import all modules to trigger their bot.add_handler() calls
    # This maintains backward compatibility with existing module structure
    from bot.modules import (
        batch,
        cancel,
        botfiles,
        copy,
        debrid,
        leech,
        mirror_leech,
        mirror_select,
        myfilesset,
        owner_settings,
        rcfm,
        stats,
        status,
        clone,
        storage,
        cleanup,
        torr_search,
        torr_select,
        user_settings,
        ytdlp,
        shell,
        exec,
        rss,
        serve,
        sync,
        gd_count,
        queue,
        tmdb,
        bisync,
    )
    from bot.helper.ext_utils.help_messages import help_callback

    LOGGER.info(f"All handlers registered")
