# Adapted from:
# Repository: github.com/anasty17/mirror-leech-telegram-bot

from os import execl as osexecl
import os
import signal
from subprocess import run as srun
from sys import executable
from bot import ALLOWED_CHATS, ALLOWED_USERS, LOGGER, OWNER_ID
from bot.utils.bot_utils.misc_utils import clean_all


async def handle_restart(message):
        user_id= message.sender_id
        chat_id= message.chat_id
        if user_id in ALLOWED_USERS or chat_id in ALLOWED_CHATS or user_id == OWNER_ID:
            restartmsg= await message.reply("Restarting...")
            try:
                for line in os.popen("ps ax | grep " + "rclone" + " | grep -v grep"):
                    fields = line.split()
                    pid = fields[0]
                    os.kill(int(pid), signal.SIGKILL)
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
    

    