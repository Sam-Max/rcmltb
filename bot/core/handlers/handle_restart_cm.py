from os import execl as osexecl
import os
import signal
from subprocess import run as srun
from sys import executable

async def handle_restart(e):
    update_message= await e.reply("Restarting...")

    try:
        for line in os.popen("ps ax | grep " + "rclone" + " | grep -v grep"):
            fields = line.split()
            pid = fields[0]
            os.kill(int(pid), signal.SIGKILL)
    except:
        print("Error Encountered")

    srun(["python3", "update.py"])

    with open(".updatemsg", "w") as f:
        f.truncate(0)
        f.write(f"{update_message.peer_id.user_id}\n{update_message.id}\n")

    osexecl(executable, executable, "-m", "bot")

    