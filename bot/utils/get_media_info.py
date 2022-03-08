# Adapted from:
# Repository: github.com/anasty17/mirror-leech-telegram-bot
# mirror-leech-telegram-bot\bot\helper\ext_utils\fs_utils.py

from logging import Logger
from subprocess import check_output
from json import loads

def get_m_info(path):
    try:
        result = check_output(["ffprobe", "-hide_banner", "-loglevel", "error", "-print_format",
                                          "json", "-show_format", path]).decode('utf-8')
        fields = loads(result)['format']
    except Exception as e:
        Logger.error(f"get_media_info: {e}")
        return 0, None, None
    try:
        duration = round(float(fields['duration']))
    except:
        duration = 0
    try:
        artist = str(fields['tags']['artist'])
    except:
        artist = None
    try:
        title = str(fields['tags']['title'])
    except:
        title = None
    return duration, artist, title