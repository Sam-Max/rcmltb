from pyrogram.filters import command
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
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
    buttons.url_buildbutton("GitHub", "https://github.com/Sam-Max/rcmltb")
    buttons.url_buildbutton("Developer", "https://github.com/Sam-Max")
    reply_markup = buttons.build_menu(2)
    if CustomFilters.user_filter or CustomFilters.chat_filter:
        msg = (
            "🤖 <b>RCMLTB Bot</b>\n\n"
            "📥 Mirror, Leech, and Transfer files between cloud storage and Telegram.\n\n"
            "<b>Features:</b>\n"
            "🔄 Mirror to Google Drive / Rclone remotes\n"
            "📤 Leech to Telegram\n"
            "🧲 Torrent / Magnet / Direct link support\n"
            "🎬 YT-DLP video downloads\n"
            "📋 Rclone copy / sync / bisync\n"

            "🎥 TMDB search\n\n"
            "📚 Use /help for available commands."
        )
        await sendMarkup(msg, message, reply_markup)
    else:
        await sendMarkup(
            "🚫 <b>Access Denied</b>\n\nYou are not authorized. Deploy your own instance.",
            message,
            reply_markup,
        )


async def restart(_, message):
    from bot import Interval

    restart_msg = await sendMessage("🔄 <b>Restarting...</b>", message)
    if Interval:
        for intvl in list(Interval.values()):
            intvl.cancel()
    await clean_all()
    await (
        await create_subprocess_exec(
            "pkill", "-9", "-f", "gunicorn|aria2c|rclone|qbittorrent-nox|ffmpeg|yt-dlp"
        )
    ).wait()
    await (await create_subprocess_exec("python3", "update.py")).wait()
    async with aiopen(".restartmsg", "w") as f:
        await f.write(f"{restart_msg.chat.id}\n{restart_msg.id}\n")
    osexecl(executable, executable, "-m", "bot")


async def ping(_, message):
    start_time = int(round(time() * 1000))
    reply = await sendMessage("🏓 <b>Pong!</b>", message)
    end_time = int(round(time() * 1000))
    await editMessage(f"<b>Latency:</b> {end_time - start_time} ms", reply)


async def get_ip(_, message):
    stdout, stderr, code = await cmd_exec("curl https://api.ipify.org/", shell=True)
    if code == 0:
        await message.reply_text(f"<b>Server IP:</b> <code>{stdout.strip()}</code>")
    else:
        await message.reply_text(f"<b>Error:</b> {stderr}")


async def get_log(client, message):
    await client.send_document(
        chat_id=message.chat.id,
        document="botlog.txt",
        caption="📋 <b>Bot Log File</b>",
    )


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
        help,
        copy,
        force_start,
        leech,
        mediainfo,
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
        serve,
        sync,
        gd_count,
        queue,
        tmdb,
        bisync,
    )

    # Register force_start handler
    from bot.modules.force_start import remove_from_queue
    bot.add_handler(
        MessageHandler(
            remove_from_queue,
            filters=command(BotCommands.ForceStartCommand)
            & (CustomFilters.user_filter | CustomFilters.chat_filter),
        )
    )

    # Register improved torr_select handler
    from bot.modules.torr_select import select as torr_select_handler
    bot.add_handler(
        MessageHandler(
            torr_select_handler,
            filters=command(BotCommands.SelectCommand)
            & (CustomFilters.user_filter | CustomFilters.chat_filter),
        )
    )

    from bot.helper.ext_utils.help_messages import help_callback

    LOGGER.info(f"All handlers registered")
