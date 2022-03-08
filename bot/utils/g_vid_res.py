# Adapted from:
# Repository: github.com/anasty17/mirror-leech-telegram-bot/
# mirror-leech-telegram-bot/bot/helper/ext_utils/fs_utils.py

from json import loads as jsnloads
import logging
from subprocess import check_output

def get_video_resolution(path):
    try:
        result = check_output(["ffprobe", "-hide_banner", "-loglevel", "error", "-select_streams", "v:0",
                                          "-show_entries", "stream=width,height", "-of", "json", path]).decode('utf-8')
        fields = jsnloads(result)['streams'][0]

        width = int(fields['width'])
        height = int(fields['height'])
        return width, height
    except Exception as e:
        logging.error(f"get_video_resolution: {e}")
        return 480, 320