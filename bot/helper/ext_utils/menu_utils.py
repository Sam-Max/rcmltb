
from bot.helper.ext_utils.human_format import get_readable_file_size
from bot.helper.ext_utils.rclone_data_holder import update_rclone_data


class Menus:
    LEECH= "leechmenu"
    COPY= "copymenu"
    MYFILES= "myfilesmenu"
    CLOUDSEL= "cloudselectmenu" 

def rcloneListNextPage(list_info, offset= 0, max_results=10):
    start = offset
    end = max_results + start
    next_offset = offset + max_results

    if end > len(list_info):
        next_list_info = list_info[offset:]    
    elif offset >= len(list_info):
        next_list_info= []    
    else:
        next_list_info= list_info[start:end]  

    return next_list_info, next_offset

def rcloneListButtonMaker(result_list, buttons, menu_type, dir_callback, file_callback, user_id):
    for index, dir in enumerate(result_list):
        path = dir["Path"]
        update_rclone_data(str(index), path, user_id)
        size= dir['Size']
        size= get_readable_file_size(size)

        if dir['MimeType'] == 'inode/directory': 
            buttons.cb_buildbutton(f"📁 {path}", data= f"{menu_type}^{dir_callback}^{index}^{user_id}") 
        else:
            buttons.cb_buildbutton(f"[{size}] {path}", data= f"{menu_type}^{file_callback}^{index}^True^{user_id}")
