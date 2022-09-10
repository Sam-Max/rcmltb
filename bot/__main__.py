from bot import OWNER_ID, ALLOWED_CHATS, ALLOWED_USERS, LOGGER, bot, Bot
from os import path as ospath, remove as osremove, execl as osexecl, kill, popen
from pyrogram.filters import command
from pyrogram.handlers import MessageHandler
from signal import SIGKILL
from sys import executable
from subprocess import run as srun
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.filters import CustomFilters
from bot.helper.ext_utils.message_utils import sendMarkup, sendMessage
from bot.helper.ext_utils.misc_utils import ButtonMaker, clean_all, start_cleanup
from bot.modules import batch, cancel, config, copy, leech, leechset, mirror, mirrorset, search, myfiles, myfiles_settings, server, speedtest, status, gclone, storage, cleanup

print("Successfully deployed!")

async def start_handler(client, message):
    user_id= message.from_user.id
    if user_id in ALLOWED_USERS or message.chat.id  in ALLOWED_CHATS or user_id == OWNER_ID:
        buttons = ButtonMaker()
        buttons.url_buildbutton("Repo", "https://github.com/Sam-Max/Rclone-Tg-Bot")
        buttons.url_buildbutton("Owner", "https://github.com/Sam-Max")
        reply_markup = buttons.build_menu(2)
        msg = '''
**Hello, ¡Welcome to Rclone-Tg-Bot!\n
I can help you copy files from one cloud to another.
I can also can mirror-leech files and links to Telegram or cloud**\n\n
        '''
        await sendMarkup(msg, message, reply_markup)
    else:
        await sendMarkup("Not Authorized user, deploy your own version", message, reply_markup)     
    
async def handle_restart(client, message):
    restart_msg= await sendMessage("Restarting...", message) 
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

async def get_logs(client, message):
    await client.send_document(chat_id= message.chat.id , document= "botlog.txt")

async def main():
    start_cleanup()
    if ospath.isfile(".restartmsg"):
        with open(".restartmsg") as f:
            cht_id, msg_id = map(int, f)
        await Bot.edit_message_text(text= "Restarted successfully!", message_id= msg_id,
                                chat_id= cht_id)     
        osremove(".restartmsg")

    start = MessageHandler(start_handler, filters= command(BotCommands.StartCommand))
    restart = MessageHandler(handle_restart, filters= command(BotCommands.RestartCommand) & CustomFilters.user_filter | CustomFilters.chat_filter)
    logs = MessageHandler(get_logs, filters= command(BotCommands.LogsCommand) & CustomFilters.user_filter | CustomFilters.chat_filter)

    Bot.add_handler(start)
    Bot.add_handler(restart)
    Bot.add_handler(logs)

    await Bot.send_message(OWNER_ID, text="The bot is ready to use")

bot.loop.run_until_complete(main())

try:
    bot.loop.run_until_complete()
except:
    pass

bot.run_until_disconnected()

