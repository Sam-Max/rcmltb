from bot import OWNER_ID, ALLOWED_CHATS, ALLOWED_USERS, LOGGER, bot, Bot
from os import path as ospath, remove as osremove, execl as osexecl, kill, popen
from telethon.events import NewMessage
from signal import SIGKILL
from sys import executable
from subprocess import run as srun
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.bot_utils import command_process
from bot.helper.ext_utils.misc_utils import clean_all, start_cleanup
from bot.modules import batch, cancel, config, copy, leech, leechset, mirror, mirrorset, search, myfiles, myfiles_settings, server, speedtest, status, gclone 

print("Successfully deployed!")

async def start_handler(message):
        user_id= message.sender_id
        chat_id= message.chat_id
        if user_id in ALLOWED_USERS or chat_id in ALLOWED_CHATS or user_id == OWNER_ID:
            msg = '''**Hello, ¡Welcome to Rclone-Tg-Bot!\n
    I can help you copy files from one cloud to another.
    Also can mirror files from Telegram to cloud and leech from cloud to Telegram**\n\n
    Repository: https://github.com/Sam-Max/Rclone-Tg-Bot
    '''
            await message.reply(msg)
        else:
            await message.reply('Not Authorized user, deploy your own version\n\nhttps://github.com/Sam-Max/Rclone-Tg-Bot')
        
async def handle_restart(message):
        user_id= message.sender_id
        chat_id= message.chat_id
        if user_id in ALLOWED_USERS or chat_id in ALLOWED_CHATS or user_id == OWNER_ID:
            restartmsg= await message.reply("Restarting...")
            try:
                for line in popen("ps ax | grep " + "rclone" + " | grep -v grep"):
                    fields = line.split()
                    pid = fields[0]
                    kill(int(pid), SIGKILL)
            except Exception as exc:
                LOGGER.info(f"Error: {exc}")
            with open(".restartmsg", "w") as f:
                f.truncate(0)
                f.write(f"{chat_id}\n{restartmsg.id}\n")
            clean_all()
            srun(["pkill", "-f", "gunicorn|aria2c|megasdkrest|qbittorrent-nox"])
            srun(["python3", "update.py"])
            osexecl(executable, executable, "-m", "bot")
        else:
            await message.reply('Not Authorized user')  

async def get_logs(e):
    if e.sender_id == OWNER_ID:
        await e.client.send_file(entity= e.chat_id,
            file= "botlog.txt",
            reply_to= e.message.id)
    else:
        await e.reply('Not Authorized user') 

async def main():
    start_cleanup()
    if ospath.isfile(".restartmsg"):
        with open(".restartmsg") as f:
            cht_id, msg_id = map(int, f)
        await Bot.edit_message_text(text= "Restarted successfully!", message_id= msg_id,
                                chat_id= cht_id)     
        osremove(".restartmsg")
    bot.add_event_handler(start_handler, NewMessage(pattern= command_process(f"/{BotCommands.StartCommand}")))
    bot.add_event_handler(handle_restart, NewMessage(pattern= command_process(f"/{BotCommands.RestartCommand}")))
    bot.add_event_handler(get_logs, NewMessage(pattern=command_process(f"/{BotCommands.LogsCommand}")))
    await Bot.send_message(OWNER_ID, text="The bot is ready to use")

bot.loop.run_until_complete(main())

try:
    bot.loop.run_until_complete()
except:
    pass

bot.run_until_disconnected()

