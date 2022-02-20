import logging
import os

async def rename(old_path, new_name):
    #os.chdir("Downloads")
    file_name, file_extension = os.path.splitext(old_path)
    #name = file_name.split("/")[-1]
    #old_name= name + file_extension
    new_name= new_name + file_extension
    new_path= os.path.join(os.getcwd(), "Downloads", new_name)
    logging.info(os.getcwd())
    logging.info(new_path)
    os.rename(old_path, new_path)
    #path = os.path.join(os.getcwd(), new_name) 
    return new_path

    