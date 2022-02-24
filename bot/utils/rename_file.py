import logging
import os

async def rename(old_path, new_name):
    _, file_extension = os.path.splitext(old_path)
    new_name= new_name + file_extension
    new_path= os.path.join(os.getcwd(), "Downloads", new_name)
    logging.info(old_path)
    logging.info(new_path)
    os.rename(old_path, new_path)
    return new_path

    