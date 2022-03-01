from os import execl as osexecl
from subprocess import run as srun
from sys import executable

async def update(e):
    update_message= await e.reply("Updating...")

    srun(["python3", "update.py"])

    with open(".updatemsg", "w") as f:
        f.truncate(0)
        f.write(f"{update_message.peer_id.user_id}\n{update_message.id}\n")

    osexecl(executable, executable, "-m", "bot")

    