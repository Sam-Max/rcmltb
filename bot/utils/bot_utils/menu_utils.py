from bot.core.varholderwrap import set_val
from bot.utils.bot_utils.human_format import get_readable_file_size

folder_icon= "📁"

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

def rcloneListButtonMaker(result_list, buttons, menu_type, callback, is_second_menu= ""):
    for index, dir in enumerate(result_list):
        path = dir["Path"]
        set_val(f'{index}', path)
        size= dir['Size']
        size= get_readable_file_size(size)
        mime_type= dir['MimeType']
         
        if menu_type == Menus.LEECH:
           file_action= "start_leech_file"  
        elif menu_type == Menus.COPY:
           if is_second_menu:
                file_action= "start_copy"   
           else:
                file_action= "list_drive_second_menu"   
        elif menu_type == Menus.MIRRORSET:
            if mime_type == 'inode/directory': 
                buttons.cbl_buildbutton(f"{folder_icon} {path}", data= f"{menu_type}^{callback}^{index}") 
                continue
        elif menu_type == Menus.MYFILES:
            file_action= "start_file_actions"       

        if mime_type == 'inode/directory': 
            buttons.cbl_buildbutton(f"{folder_icon} {path}", data= f"{menu_type}^{callback}^{index}") 
        else:
            buttons.cbl_buildbutton(f"[{size}] {path}", data= f"{menu_type}^{file_action}^{index}^True")
