
from bot.helper.ext_utils.human_format import get_readable_file_size
from bot.helper.ext_utils.var_holder import update_rclone_var


class Menus:
    LEECH= "leechmenu"
    COPY= "copymenu"
    MYFILES= "myfilesmenu"
    MIRRORSET= "mirrorsetmenu" 

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

def rcloneListButtonMaker(result_list, buttons, menu_type, callback, user_id, is_second_menu=False):
    for index, dir in enumerate(result_list):
        path = dir["Path"]
        size= dir['Size']
        mime_type= dir['MimeType']
        update_rclone_var(str(index), path, user_id)
        size= get_readable_file_size(size)

        if menu_type == Menus.LEECH:
            file_action= "leech_file"  
        elif menu_type == Menus.MYFILES:
            file_action= "file_actions"  
        elif menu_type == Menus.COPY:
            if is_second_menu:
                file_action= "copy"   
            else:
                file_action= "drive_second"   
        else:
            file_action= ''
         
        if mime_type == 'inode/directory': 
            buttons.cb_buildbutton(f"📁 {path}", data= f"{menu_type}^{callback}^{index}^{user_id}") 
        else:
            buttons.cb_buildbutton(f"[{size}] {path}", data= f"{menu_type}^{file_action}^{index}^True^{user_id}")
