import os
import signal

async def handle_cancel_all(e):
    try:
        for line in os.popen("ps ax | grep " + "rclone" + " | grep -v grep"):
            fields = line.split()
            pid = fields[0]
            os.kill(int(pid), signal.SIGKILL)
            await e.answer("Upload has been canceled ", alert=True)
    except:
        print("Error Encountered")