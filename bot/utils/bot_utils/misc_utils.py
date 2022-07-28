import os
from shutil import rmtree
from bot import LOGGER
from itertools import zip_longest
from json import loads as jsnloads
import os
from subprocess import check_output
from subprocess import check_output
from json import loads

def pairwise(iterable):
    "s -> (s0, s1), (s2, s3), (s4, s5), ..."
    a = iter(iterable)
    return zip_longest(a, a)

def clean_path(path):
    if os.path.exists(path):
        LOGGER.info(f"Cleaning Download: {path}")
        try:
           rmtree(path)
        except:
            pass

def clean_filepath(file_path):
     LOGGER.info(f"Cleaning Download: {file_path}")
     try:
        os.remove(file_path)
     except:
        pass

def rename_file(old_path, new_name):
    _, file_extension = os.path.splitext(old_path)
    new_name= new_name + file_extension
    new_path= os.path.join(os.getcwd(), "Downloads", new_name)
    os.rename(old_path, new_path)
    return new_path

def get_rclone_config():
    rclone_conf = os.path.join(os.getcwd(), 'rclone.conf')
    if rclone_conf is not None:
        if isinstance(rclone_conf, str):
            if os.path.exists(rclone_conf):
                return rclone_conf
    return None

def get_readable_size(size):
    """Get size in readable format"""

    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i]) 

def get_media_info(path):
    try:
        result = check_output(["ffprobe", "-hide_banner", "-loglevel", "error", "-print_format",
                                            "json", "-show_format", path]).decode('utf-8')
        fields = loads(result)['format']
    except Exception as e:
        LOGGER.error(f"get_media_info: {e}")
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

def get_video_resolution(path):
    try:
        result = check_output(["ffprobe", "-hide_banner", "-loglevel", "error", "-select_streams", "v:0",
                                          "-show_entries", "stream=width,height", "-of", "json", path]).decode('utf-8')
        fields = jsnloads(result)['streams'][0]

        width = int(fields['width'])
        height = int(fields['height'])
        return width, height
    except Exception as e:
        LOGGER.error(f"get_video_resolution: {e}")
        return 480, 320

