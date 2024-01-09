from asyncio import create_subprocess_exec
from signal import signal, SIGINT
from aiofiles import open as aiopen
from time import time
from bot import (
    LOGGER,
    Interval,
    QbInterval,
    bot,
    bot_loop,
    scheduler,
)
from os import path as ospath, remove as osremove, execl as osexecl
from bot.helper.ext_utils.help_messages import (
    create_batch_help_buttons,
    create_leech_help_buttons,
    create_mirror_help_buttons,
    create_ytdl_help_buttons,
)
from pyrogram.filters import command
from pyrogram.handlers import MessageHandler
from sys import executable
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.mirror_leech_utils.download_utils.aria2_download import (
    start_aria2_listener,
)
from .helper.telegram_helper.bot_commands import BotCommands
from .helper.ext_utils.bot_utils import cmd_exec, run_sync_to_async
from json import loads
from .helper.telegram_helper.filters import CustomFilters
from .helper.telegram_helper.message_utils import editMessage, sendMarkup, sendMessage
from .helper.ext_utils.misc_utils import clean_all, exit_clean_up, start_cleanup
from .modules import (
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
)


async def start(_, message):
    buttons = ButtonMaker()
    buttons.url_buildbutton("Repo", "https://github.com/Sam-Max/rcmltb")
    buttons.url_buildbutton("Owner", "https://github.com/Sam-Max")
    reply_markup = buttons.build_menu(2)
    if CustomFilters.user_filter or CustomFilters.chat_filter:
        msg = """
**Hello, ¡Welcome to Rclone-Telegram-Bot!\n
I can help you copy files from one cloud to another.
I can also can mirror-leech files and links to Telegram or cloud**\n\n
        """
        await sendMarkup(msg, message, reply_markup)
    else:
        await sendMarkup(
            "Not Authorized user, deploy your own version", message, reply_markup
        )


async def restart(_, message):
    restart_msg = await sendMessage("Restarting...", message)
    if scheduler.running:
        scheduler.shutdown(wait=False)
    if Interval:
        for intvl in list(Interval.values()):
            intvl.cancel()
    if QbInterval:
        QbInterval[0].cancel()
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


async def main():
    await start_cleanup()

    await create_mirror_help_buttons()
    await create_ytdl_help_buttons()
    await create_leech_help_buttons()
    await create_batch_help_buttons()

    await torr_search.initiate_search_tools()
    await debrid.load_debrid_token()
    await run_sync_to_async(start_aria2_listener, wait=False)

    if ospath.isfile(".restartmsg"):
        with open(".restartmsg") as f:
            chat_id, msg_id = map(int, f)
        try:
            await bot.edit_message_text(chat_id, msg_id, "Restarted successfully!")
        except:
            pass
        osremove(".restartmsg")

    bot.add_handler(MessageHandler(start, filters=command(BotCommands.StartCommand)))
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
    bot.add_handler(MessageHandler(get_ip, filters=command(BotCommands.IpCommand)))
    LOGGER.info("Bot Started!")
    signal(SIGINT, exit_clean_up)


bot_loop.run_until_complete(main())
bot_loop.run_forever()
