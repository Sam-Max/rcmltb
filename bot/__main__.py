from asyncio import create_subprocess_exec
from signal import signal, SIGINT
from time import time
from bot import LOGGER, Interval, QbInterval, bot, botloop, scheduler
from os import path as ospath, remove as osremove, execl as osexecl
from pyrogram.filters import command
from pyrogram.handlers import MessageHandler
from sys import executable
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.mirror_leech_utils.download_utils.aria2_download import start_aria2_listener
from .helper.telegram_helper.bot_commands import BotCommands
from .helper.ext_utils.bot_utils import cmd_exec, run_sync
from json import loads
from .helper.telegram_helper.filters import CustomFilters
from .helper.telegram_helper.message_utils import editMessage, sendMarkup, sendMessage
from .helper.ext_utils.misc_utils import clean_all, exit_clean_up, start_cleanup
from .helper.ext_utils import db_handler
from .modules import batch, cancel, botfiles, copy, leech, mirror_leech, mirror_select, myfilesset, owner_settings, myfiles, search, stats, status, clone, storage, cleanup, user_settings, ytdlp, shell, exec, bt_select, rss, serve, sync, tmdb


start_aria2_listener()


async def start(client, message):
    buttons = ButtonMaker()
    buttons.url_buildbutton("Repo", "https://github.com/Sam-Max/rcmltb")
    buttons.url_buildbutton("Owner", "https://github.com/Sam-Max")
    reply_markup = buttons.build_menu(2)
    if CustomFilters.user_filter or CustomFilters.chat_filter:
        msg = '''
**Hello, ¡Welcome to Rclone-Telegram-Bot!\n
I can help you copy files from one cloud to another.
I can also can mirror-leech files and links to Telegram or cloud**\n\n
        '''
        await sendMarkup(msg, message, reply_markup)
    else:
        await sendMarkup("Not Authorized user, deploy your own version", message, reply_markup)     
    
async def restart(client, message):
    restart_msg= await sendMessage("Restarting...", message) 
    if scheduler.running:
        scheduler.shutdown(wait=False)
    if Interval:
        Interval[0].cancel()
        Interval.clear()
    if QbInterval:
        QbInterval[0].cancel()
        QbInterval.clear()
    await run_sync(clean_all)
    await (await create_subprocess_exec("pkill", "-9", "-f", "gunicorn|aria2c|rclone|qbittorrent-nox|ffmpeg")).wait()
    await (await create_subprocess_exec("python3", "update.py")).wait()
    with open(".restartmsg", "w") as f:
        f.truncate(0)
        f.write(f"{restart_msg.chat.id}\n{restart_msg.id}\n")
    osexecl(executable, executable, "-m", "bot")

async def ping(client, message):
    start_time = int(round(time() * 1000))
    reply = await sendMessage("Starting Ping", message)
    end_time = int(round(time() * 1000))
    await editMessage(f'{end_time - start_time} ms', reply)

async def get_ip(client, message):
    stdout, stderr, return_code = await cmd_exec("curl https://ifconfig.me/all.json", shell=True)
    if return_code == 0:
        res= loads(stdout)
        msg= f"Your IP is {res['ip_addr']}"
        await message.reply_text(msg)
    else:
        LOGGER.info(f'Error: {stderr}')

async def get_log(client, message):
    await client.send_document(chat_id= message.chat.id , document= "botlog.txt")

async def main():
    await start_cleanup()
    await search.initiate_search_tools()
    if ospath.isfile(".restartmsg"):
        with open(".restartmsg") as f:
            chat_id, msg_id = map(int, f)
        try:
            await bot.edit_message_text(chat_id, msg_id, "Restarted successfully!")  
        except:
            pass   
        osremove(".restartmsg")
            
    bot.add_handler(MessageHandler(start, filters= command(BotCommands.StartCommand)))
    bot.add_handler(MessageHandler(restart, filters= command(BotCommands.RestartCommand) & (CustomFilters.owner_filter | CustomFilters.sudo_filter)))
    bot.add_handler(MessageHandler(get_log, filters= command(BotCommands.LogsCommand) & (CustomFilters.owner_filter | CustomFilters.sudo_filter)))
    bot.add_handler(MessageHandler(ping, filters= command(BotCommands.PingCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter)))
    bot.add_handler(MessageHandler(get_ip, filters= command(BotCommands.IpCommand)))
    LOGGER.info("Bot Started!")
    signal(SIGINT, exit_clean_up)

botloop.run_until_complete(main())
botloop.run_forever()

