import os
from shutil import rmtree
from bot import LOGGER
from itertools import zip_longest

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

async def get_rclone_config():
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

