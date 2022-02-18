import os

async def rename(path, new_name):
    os.chdir("Downloads")
    file_name, file_extension = os.path.splitext(path)
    name = file_name.split("/")[-1]
    old_name= name + file_extension
    new_name= new_name + file_extension
    os.rename(old_name, new_name)
    path = os.path.join(os.getcwd(), new_name) 
    return path
    