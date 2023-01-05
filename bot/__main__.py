from time import time
from bot import Interval, QbInterval, bot, botloop, app, bot
from os import path as ospath, remove as osremove, execl as osexecl
from pyrogram.filters import command
from pyrogram.handlers import MessageHandler
from sys import executable
from subprocess import run as srun
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.filters import CustomFilters
from bot.helper.ext_utils.message_utils import editMessage, sendMarkup, sendMessage
from bot.helper.ext_utils.misc_utils import ButtonMaker, clean_all, start_cleanup
from bot.helper.ext_utils import db_handler
from bot.modules import batch, cancel, botfiles, copy, leech, mirror_leech, myfilesset, owner_settings, cloudselect, search, myfiles, stats, status, clone, storage, cleanup, user_settings, ytdlp, shell, exec, bt_select, rss, serve, sync


print("Successfully deployed!!")

async def start(client, message):
    buttons = ButtonMaker()
    buttons.url_buildbutton("Repo", "https://github.com/Sam-Max/rclone-mirror-leech-telegram-bot")
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
    if Interval:
        Interval[0].cancel()
        Interval.clear()
    if QbInterval:
        QbInterval[0].cancel()
        QbInterval.clear()
    clean_all()
    srun(["pkill", "-9", "-f", "gunicorn|aria2c|rclone|qbittorrent-nox|ffmpeg"])
    srun(["python3", "update.py"])
    with open(".restartmsg", "w") as f:
        f.truncate(0)
        f.write(f"{restart_msg.chat.id}\n{restart_msg.id}\n")
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
            chat_id, msg_id = map(int, f)
        try:
            await bot.edit_message_text(chat_id, msg_id, "Restarted successfully!")  
        except:
            pass   
        osremove(".restartmsg")
            
    start_handler = MessageHandler(start, filters= command(BotCommands.StartCommand))
    restart_handler = MessageHandler(restart, filters= command(BotCommands.RestartCommand) & (CustomFilters.owner_filter | CustomFilters.sudo_filter))
    log_handler = MessageHandler(get_log, filters= command(BotCommands.LogsCommand) & (CustomFilters.owner_filter | CustomFilters.sudo_filter))
    ping_handler = MessageHandler(ping, filters= command(BotCommands.PingCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter))
   
    bot.add_handler(start_handler)
    bot.add_handler(restart_handler)
    bot.add_handler(log_handler)
    bot.add_handler(ping_handler)

bot.start()
if app is not None:
    app.start()
    
botloop.run_until_complete(main())
botloop.run_forever()

