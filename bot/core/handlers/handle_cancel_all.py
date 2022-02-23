import os
import signal

async def handle_cancel_all(e):
    try:
        # iterating through each instance of the process
        for line in os.popen("ps ax | grep " + "rclone" + " | grep -v grep"):
            fields = line.split()

            # extracting Process ID from the output
            pid = fields[0]

            # terminating process
            os.kill(int(pid), signal.SIGKILL)

            await e.answer("Upload has been canceled ", alert=True)
    except:
        print("Error Encountered while running script")