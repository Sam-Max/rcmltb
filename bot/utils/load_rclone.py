import logging 
import os

def load_rclone():
    path = os.path.join(os.getcwd(), "rclone.conf")
    rclone_config = os.environ.get('RCLONE_CONFIG', "")  
    if len(rclone_config) == 0:                                         
        logging.info(f'rclone_config:0')                                          
    else:
        logging.info(f'rclone_config:1')           
        rclone_config.strip()
        str_1_encoded = bytes(rclone_config,'UTF-8')

        with open(path, "wb") as rfile:
            rfile.write(str_1_encoded)

    return path