import os
from bot import SessionVars

async def get_rclone():

    path = os.path.join(os.getcwd(), "rclone.conf")

    rclone_config= SessionVars.get_var("RCLONE_CONFIG")
    rclone_config.strip()
    str_1_encoded = bytes(rclone_config,'UTF-8')

    with open(path, "wb") as rfile:
        rfile.write(str_1_encoded)

    return path