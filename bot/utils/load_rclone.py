import logging 
import os

def load_rclone():
    path = os.path.join(os.getcwd(), "rclone.conf")
    rclone_config = os.environ.get('RCLONE_CONFIG', "")  
    if rclone_config:                                         
        rclone_config.strip()
        str_encoded = bytes(rclone_config,'UTF-8')
        with open(path, "wb") as rfile:
            rfile.write(str_encoded)
        logging.info(f'rclone file loaded')    
    else:
        logging.info(f'faile to load rclone file')     