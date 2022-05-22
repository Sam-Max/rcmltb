import logging
import os
import shutil

log = logging.getLogger(__name__)

def clean_path(path):
    if os.path.exists(path):
        log.info(f"Cleaning Download: {path}")
        try:
           shutil.rmtree(path)
        except:
            pass

def clean_filepath(file_path):
     log.info(f"Cleaning Download: {file_path}")
     try:
        os.remove(file_path)
     except:
        pass
