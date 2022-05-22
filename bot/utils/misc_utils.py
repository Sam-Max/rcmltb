import os
import shutil


def clean_all():
    try:
        shutil.rmtree("./Downloads")
    except:
        pass

def clean_download(path: str):
     if os.path.exists(path):
        try:
            shutil.rmtree(path)
        except:
            pass
        os.makedirs(path)
