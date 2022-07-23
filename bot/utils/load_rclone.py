import logging 
import os

def load_rclone():
    rclone_config = os.environ.get('RCLONE_CONFIG', "")  
    if rclone_config:                                         
        rclone_config.strip()
        str_encoded = bytes(rclone_config,'UTF-8')
        with open(os.path.join(os.getcwd(), "rclone.conf"), "wb") as rfile:
            rfile.write(str_encoded)
        logging.info(f'Rclone file loaded!!')    
    else:
        logging.info(f'Failed to load rclone file!!')     