import os
from shutil import rmtree

from bot import LOGGER

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

