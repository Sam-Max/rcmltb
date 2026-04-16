from os import path as ospath
from aiofiles.os import path as aiopath, makedirs
from time import time
from json import loads as jsnloads
from bot import LOGGER
from bot.helper.ext_utils.bot_utils import cmd_exec
from bot.helper.ext_utils.misc_utils import get_media_info


async def get_detailed_media_info(path):
    """
    Returns dict with detailed media information using ffprobe.
    {
        'duration': seconds,
        'bitrate': kbps,
        'size': bytes,
        'format': container_format,
        'video': {
            'codec': str,
            'width': int,
            'height': int,
            'fps': float,
            'bitrate': kbps
        },
        'audio': [{
            'codec': str,
            'channels': int,
            'sample_rate': hz,
            'language': str
        }],
        'subtitles': [{
            'language': str,
            'format': str
        }]
    }
    """
    try:
        result = await cmd_exec(
            [
                "ffprobe",
                "-hide_banner",
                "-loglevel",
                "error",
                "-print_format",
                "json",
                "-show_streams",
                "-show_format",
                path,
            ]
        )
        if result[2] != 0:
            LOGGER.error(f"ffprobe error: {result[1]}")
            return None
    except Exception as e:
        LOGGER.error(f"Get Detailed Media Info: {e}")
        return None

    try:
        data = jsnloads(result[0])
    except Exception as e:
        LOGGER.error(f"JSON parse error: {e}")
        return None

    info = {
        "duration": 0,
        "bitrate": 0,
        "size": 0,
        "format": "Unknown",
        "video": None,
        "audio": [],
        "subtitles": [],
    }

    # Parse format info
    format_data = data.get("format", {})
    if format_data:
        info["duration"] = round(float(format_data.get("duration", 0)))
        info["bitrate"] = int(format_data.get("bit_rate", 0)) // 1000
        info["size"] = int(format_data.get("size", 0))
        info["format"] = format_data.get("format_long_name", "Unknown")

    # Parse streams
    streams = data.get("streams", [])
    for stream in streams:
        stream_type = stream.get("codec_type")

        if stream_type == "video":
            info["video"] = {
                "codec": stream.get("codec_name", "Unknown").upper(),
                "width": stream.get("width", 0),
                "height": stream.get("height", 0),
                "fps": eval(stream.get("r_frame_rate", "0/1")),
                "bitrate": int(stream.get("bit_rate", 0)) // 1000,
            }
        elif stream_type == "audio":
            audio_info = {
                "codec": stream.get("codec_name", "Unknown").upper(),
                "channels": stream.get("channels", 0),
                "sample_rate": stream.get("sample_rate", 0),
                "language": stream.get("tags", {}).get("language", "Unknown"),
            }
            info["audio"].append(audio_info)
        elif stream_type == "subtitle":
            sub_info = {
                "language": stream.get("tags", {}).get("language", "Unknown"),
                "format": stream.get("codec_name", "Unknown").upper(),
            }
            info["subtitles"].append(sub_info)

    return info


def format_media_info(info, filename):
    """Format media info dict to readable message."""
    if not info:
        return "❌ <b>Failed to get media info</b>"

    from bot.helper.ext_utils.human_format import get_readable_file_size

    # Format duration
    duration = info["duration"]
    hours = duration // 3600
    minutes = (duration % 3600) // 60
    seconds = duration % 60
    duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours > 0 else f"{minutes:02d}:{seconds:02d}"

    msg = f"""📊 <b>MediaInfo</b>

<b>File:</b> <code>{filename}</code>
<b>Size:</b> {get_readable_file_size(info["size"])}
<b>Duration:</b> {duration_str}
<b>Container:</b> {info["format"]}
"""

    # Video info
    if info["video"]:
        video = info["video"]
        resolution = f"{video['width']}x{video['height']}"
        if video["width"] >= 3840:
            resolution += " (4K)"
        elif video["width"] >= 1920:
            resolution += " (1080p)"
        elif video["width"] >= 1280:
            resolution += " (720p)"

        msg += f"""
🎬 <b>Video</b>
<code>Codec: {video['codec']}
Resolution: {resolution}
Frame Rate: {video['fps']:.3f} fps
Bitrate: {video['bitrate']} kbps</code>
"""

    # Audio info
    for i, audio in enumerate(info["audio"], 1):
        channels_str = ""
        if audio["channels"] == 1:
            channels_str = "1 (Mono)"
        elif audio["channels"] == 2:
            channels_str = "2 (Stereo)"
        elif audio["channels"] == 6:
            channels_str = "6 (5.1)"
        elif audio["channels"] == 8:
            channels_str = "8 (7.1)"
        else:
            channels_str = str(audio["channels"])

        msg += f"""
🔊 <b>Audio Track {i}</b>
<code>Codec: {audio['codec']}
Channels: {channels_str}
Language: {audio['language']}
Sample Rate: {audio['sample_rate']} Hz</code>
"""

    # Subtitle info
    if info["subtitles"]:
        msg += """
📝 <b>Subtitles</b>
<code>"""
        for i, sub in enumerate(info["subtitles"], 1):
            msg += f"{i}. {sub['language']} ({sub['format']})\n"
        msg += "</code>"

    return msg


async def take_ss(video_file, ss_nb) -> list:
    ss_nb = min(ss_nb, 10)
    duration = (await get_media_info(video_file))[0]
    if duration != 0:
        dirpath, name = video_file.rsplit("/", 1)
        name, _ = ospath.splitext(name)
        dirpath = f"{dirpath}/screenshots/"
        await makedirs(dirpath, exist_ok=True)
        interval = duration // (ss_nb + 1)
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
