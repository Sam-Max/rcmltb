from os import execl as osexecl
from shutil import rmtree
from subprocess import run as srun
from sys import executable
from bot import rcprocess

async def restart(e):
    restart_message= await e.reply("Restarting...")

    for proc in rcprocess:
         proc.kill()

    try:
        rmtree("Downloads")
    except FileNotFoundError:
        pass

    srun(["python3", "update.py"])

    with open(".restartmsg", "w") as f:
        f.truncate(0)
        f.write(f"{restart_message.peer_id.user_id}\n{restart_message.id}\n")

    osexecl(executable, executable, "-m", "bot")

    