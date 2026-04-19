from asyncio import create_subprocess_exec, gather
from signal import signal, SIGINT
from aiofiles import open as aiopen
from time import time
from os import path as ospath, remove as osremove, execl as osexecl
from sys import executable

from bot import (
    LOGGER,
    bot_loop,
    scheduler,
    config_dict,
)
from bot.core.telegram_manager import TgClient
from bot.core.startup import (
    load_settings,
    load_configurations,
    save_settings,
    update_variables,
    update_aria2_options,
    update_qbit_options,
)
from bot.core.torrent_manager import TorrentManager
from bot.helper.ext_utils.help_messages import (
    create_batch_help_buttons,
    create_leech_help_buttons,
    create_mirror_help_buttons,
    create_ytdl_help_buttons,
)
from bot.helper.ext_utils.misc_utils import clean_all, exit_clean_up, start_cleanup
from bot.helper.telegram_helper.message_utils import sendMessage
from pyrogram.types import BotCommand
from bot.helper.telegram_helper.bot_commands import BotCommands


async def main():
    # 1. Load settings from DB
    await load_settings()
    LOGGER.info("Settings loaded from database")

    # 2. Start Telegram clients (concurrently)
    await gather(TgClient.start_bot(), TgClient.start_user())
    LOGGER.info("Telegram clients started")

    # 3. Start services and load configurations
    try:
        await load_configurations()
        LOGGER.info("Configurations loaded")
    except Exception as e:
        LOGGER.warning(f"load_configurations error (non-fatal): {e}")

    # 4. Initialize TorrentManager
    await TorrentManager.initiate()
    LOGGER.info("TorrentManager initiated")

    # 5. Start cleanup
    await start_cleanup()
    LOGGER.info("Cleanup done")

    # 6. Update derived variables
    await update_variables()
    LOGGER.info("Variables updated")

    # 7. Update aria2 and qbit options
    await gather(update_aria2_options(), update_qbit_options())
    LOGGER.info("Aria2/qBittorrent options updated")

    # 8. Create help buttons and init telegraph
    from bot.helper.ext_utils.telegraph_helper import init_telegraph
    await gather(
        create_mirror_help_buttons(),
        create_ytdl_help_buttons(),
        create_leech_help_buttons(),
        create_batch_help_buttons(),
        init_telegraph(),
    )
    LOGGER.info("Help buttons and telegraph created")

    # 9. Initialize search tools and debrid
    from bot.modules import torr_search, debrid
    await gather(
        torr_search.initiate_search_tools(),
        debrid.load_debrid_token(),
    )

    # 10. Start aria2 listener
    from bot.helper.listeners.aria2_listener import add_aria2_callbacks
    add_aria2_callbacks()

    # 11. Register handlers
    from bot.core.handlers import add_handlers
    add_handlers()

    # 12. Boot JDownloader if configured
    if getattr(config_dict, "JD_EMAIL", "") and getattr(config_dict, "JD_PASSWORD", ""):
        from bot.core.jdownloader_booter import jdownloader_boot
        jdownloader_boot()
        LOGGER.info("JDownloader boot initiated")

    # 13. Handle restart message
    if ospath.isfile(".restartmsg"):
        with open(".restartmsg") as f:
            chat_id, msg_id = map(int, f)
        try:
            await TgClient.bot.edit_message_text(chat_id, msg_id, "Restarted successfully!")
        except Exception:
            pass
        osremove(".restartmsg")

    # 14. Set bot commands
    await TgClient.bot.set_bot_commands(
        [
            BotCommand(BotCommands.StartCommand, "Start the bot"),
            BotCommand(BotCommands.MirrorCommand[0], "Mirror to cloud"),
            BotCommand(BotCommands.LeechCommand[0], "Leech to Telegram"),
            BotCommand(BotCommands.CloneCommand, "Clone Google Drive files"),
            BotCommand(BotCommands.CopyCommand, "Copy files between remotes"),
            BotCommand(BotCommands.StatusCommand, "Show download status"),
            BotCommand(BotCommands.StatsCommand, "Show bot stats"),
            BotCommand(BotCommands.CancelCommand, "Cancel a task"),
            BotCommand(BotCommands.CancelAllCommand, "Cancel all tasks"),
            BotCommand(BotCommands.RssCommand, "RSS feed manager"),
            BotCommand(BotCommands.TorrentSearchCommand, "Search torrents"),
            BotCommand(BotCommands.ServeCommand, "Serve files via web"),
            BotCommand(BotCommands.UserSetCommand, "User settings"),
            BotCommand(BotCommands.OwnerSetCommand, "Owner settings"),
            BotCommand(BotCommands.PingCommand, "Ping the bot"),
            BotCommand(BotCommands.LogsCommand, "Get bot logs"),
            BotCommand(BotCommands.RestartCommand, "Restart the bot"),
            BotCommand(BotCommands.MediaInfoCommand, "Get media file information"),
            BotCommand(BotCommands.PMirrorCommand, "Mirror from private channels"),
            BotCommand(BotCommands.PLeechCommand, "Leech from private channels"),
        ]
    )

    # 15. Save settings to DB
    await save_settings()

    LOGGER.info("Bot Started!")
    signal(SIGINT, exit_clean_up)


bot_loop.run_until_complete(main())
bot_loop.run_forever()
