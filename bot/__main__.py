from time import time
from bot import OWNER_ID, ALLOWED_CHATS, LOGGER, SUDO_USERS, bot, Bot
from os import path as ospath, remove as osremove, execl as osexecl, kill, popen
from pyrogram.filters import command
from pyrogram.handlers import MessageHandler
from signal import SIGKILL
from sys import executable
from subprocess import run as srun
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.filters import CustomFilters
from bot.helper.ext_utils.message_utils import editMessage, sendMarkup, sendMessage
from bot.helper.ext_utils.misc_utils import ButtonMaker, clean_all, start_cleanup
from bot.helper.ext_utils import db_handler
from bot.modules import batch, cancel, config, copy, leech, mirror, mirrorset, myfilesset, owner_settings, search, myfiles, speedtest, stats, status, clone, storage, cleanup, user_settings, ytdlp, shell, rss

print("Successfully deployed!")

async def start(client, message):
    user_id= message.from_user.id
    buttons = ButtonMaker()
    buttons.url_buildbutton("Repo", "https://github.com/Sam-Max/Rclone-Tg-Bot")
    buttons.url_buildbutton("Owner", "https://github.com/Sam-Max")
    reply_markup = buttons.build_menu(2)
    if user_id in SUDO_USERS or user_id in ALLOWED_CHATS or user_id == OWNER_ID or message.chat.id in ALLOWED_CHATS:
        msg = '''
**Hello, ¡Welcome to Rclone-Tg-Bot!\n
I can help you copy files from one cloud to another.
I can also can mirror-leech files and links to Telegram or cloud**\n\n
        '''
        await sendMarkup(msg, message, reply_markup)
    else:
        await sendMarkup("Not Authorized user, deploy your own version", message, reply_markup)     
    
async def restart(client, message):
    restart_msg= await sendMessage("Restarting", message) 
    try:
        for line in popen("ps ax | grep " + "rclone" + " | grep -v grep"):
            fields = line.split()
            pid = fields[0]
            kill(int(pid), SIGKILL)
    except Exception as exc:
        LOGGER.info(f"Error: {exc}")
    with open(".restartmsg", "w") as f:
        f.truncate(0)
        f.write(f"{message.chat.id}\n{restart_msg.id}\n")
    clean_all()
    srun(["pkill", "-f", "gunicorn|aria2c|megasdkrest|qbittorrent-nox"])
    srun(["python3", "update.py"])
    osexecl(executable, executable, "-m", "bot")

async def ping(client, message):
    start_time = int(round(time() * 1000))
    reply = await sendMessage("Starting Ping", message)
    end_time = int(round(time() * 1000))
    await editMessage(f'{end_time - start_time} ms', reply)

async def get_log(client, message):
    await client.send_document(chat_id= message.chat.id , document= "botlog.txt")

async def main():
    start_cleanup()
    if ospath.isfile(".restartmsg"):
        with open(".restartmsg") as f:
            cht_id, msg_id = map(int, f)
        await Bot.edit_message_text(text= "Restarted successfully!", message_id= msg_id,
                                chat_id= cht_id)     
        osremove(".restartmsg")

    start_handler = MessageHandler(start, filters= command(BotCommands.StartCommand))
    restart_handler = MessageHandler(restart, filters= command(BotCommands.RestartCommand) & (CustomFilters.owner_filter | CustomFilters.sudo_filter))
    log_handler = MessageHandler(get_log, filters= command(BotCommands.LogsCommand) & (CustomFilters.owner_filter | CustomFilters.sudo_filter))
    ping_handler = MessageHandler(ping, filters= command(BotCommands.PingCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter))

    Bot.add_handler(start_handler)
    Bot.add_handler(restart_handler)
    Bot.add_handler(log_handler)
    Bot.add_handler(ping_handler)

bot.loop.run_until_complete(main())
bot.run_until_disconnected()

