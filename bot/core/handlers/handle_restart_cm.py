# Adapted from:
# Repository: github.com/anasty17/mirror-leech-telegram-bot

import logging
from os import execl as osexecl
import os
import signal
from subprocess import run as srun
from sys import executable
from bot.core.get_vars import get_val

log = logging.getLogger(__name__)

async def handle_restart(message):
        user_id= message.sender_id
        chat_id= message.chat_id
        if user_id in get_val("ALLOWED_USERS") or chat_id in get_val("ALLOWED_CHATS") or user_id == get_val("OWNER_ID"):
            update_message= await message.reply("Restarting...")
            user_id= get_val("OWNER_ID")   
            try:
                for line in os.popen("ps ax | grep " + "rclone" + " | grep -v grep"):
                    fields = line.split()
                    pid = fields[0]
                    os.kill(int(pid), signal.SIGKILL)
            except Exception as exc:
                log.info(f"Error: {exc}")
            with open(".updatemsg", "w") as f:
                f.truncate(0)
                f.write(f"{user_id}\n{update_message.id}\n")
            srun(["python3", "update.py"])
            osexecl(executable, executable, "-m", "bot")
        else:
            await message.reply('Not Authorized user')  
    

    