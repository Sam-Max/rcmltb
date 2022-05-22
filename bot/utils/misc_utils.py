import logging
import os
import shutil

log = logging.getLogger(__name__)

def clean_all():
    try:
        shutil.rmtree("./Downloads")
    except:
        pass

def clean_download(path: str):
     log.info("Cleaning path {}".format(path))
     if os.path.exists(path):
        try:
            shutil.rmtree(path)
        except:
            pass
        os.makedirs(path)
