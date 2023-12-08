from os import path as ospath
from aiofiles.os import path as aiopath, makedirs
from time import time
from bot import LOGGER
from bot.helper.ext_utils.bot_utils import cmd_exec
from bot.helper.ext_utils.misc_utils import get_media_info


async def take_ss(video_file, ss_nb) -> list:
    if ss_nb > 10:
        ss_nb = 10
    duration = (await get_media_info(video_file))[0]
    if duration != 0:
        dirpath, name = video_file.rsplit("/", 1)
        name, _ = ospath.splitext(name)
        dirpath = f"{dirpath}/screenshots/"
        await makedirs(dirpath, exist_ok=True)
        interval = duration // ss_nb + 1
        cap_time = interval
        outputs = []
        cmd = ""
        for i in range(ss_nb):
            output = f"{dirpath}SS.{name}_{i:02}.png"
            outputs.append(output)
            cmd += f'ffmpeg -hide_banner -loglevel error -ss {cap_time} -i "{video_file}" -q:v 1 -frames:v 1 "{output}"'
            cap_time += interval
            if i + 1 != ss_nb:
                cmd += " && "
        _, err, code = await cmd_exec(cmd, True)
        if code != 0:
            LOGGER.error(
                f"Error while creating sreenshots from video. Path: {video_file} stderr: {err}"
            )
            return []
        return outputs
    else:
        LOGGER.error("take_ss: Can't get the duration of video")
        return []


async def create_thumb(video_file, duration):
    des_dir = "Thumbnails"
    await makedirs(des_dir, exist_ok=True)
    des_dir = ospath.join(des_dir, f"{time()}.jpg")
    if duration is None:
        duration = (await get_media_info(video_file))[0]
    if duration == 0:
        duration = 3
    duration = duration // 2
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        str(duration),
        "-i",
        video_file,
        "-vf",
        "thumbnail",
        "-frames:v",
        "1",
        des_dir,
    ]
    _, err, code = await cmd_exec(cmd)
    if code != 0 or not await aiopath.exists(des_dir):
        LOGGER.error(
            f"Error while extracting thumbnail from video. Name: {video_file} stderr: {err}"
        )
        return None
    return des_dir
