from os import path as ospath, mkdir
from PIL import Image
from time import time
from subprocess import run as srun
from bot.helper.ext_utils.misc_utils import get_media_info


async def take_ss(video_file, duration):
    des_dir = 'Thumbnails'
    if not ospath.exists(des_dir):
        mkdir(des_dir)
    des_dir = ospath.join(des_dir, f"{time()}.jpg")
    if duration is None:
        duration = (await get_media_info(video_file))[0]
    if duration == 0:
        duration = 3
    duration = duration // 2

    status = srun(["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", str(duration),
                   "-i", video_file, "-frames:v", "1", des_dir])

    if status.returncode != 0 or not ospath.lexists(des_dir):
        return None

    with Image.open(des_dir) as img:
        img.convert("RGB").save(des_dir, "JPEG")

    return des_dir