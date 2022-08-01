from bot.core.set_vars import set_val
from bot.utils.bot_utils.misc_utils import get_readable_size
from pyrogram.types import InlineKeyboardButton

def next_page_results(list_info, offset= 0, max_results=10):
    start = offset
    end = max_results + start
    next_offset = offset + max_results

    if end > len(list_info):
        list_info= list_info[offset:]    
    elif offset >= len(list_info):
        list_info= []    
    else:
        list_info= list_info[start:end]  

    return list_info, next_offset

def menu_maker_for_rclone(list_info, menu, data_callback):
    folder = ""
    index= 0
    for dir in list_info:
        path = dir["Path"]
        index += 1
        set_val(f"{index}", path)
        size= dir['Size']
        size= get_readable_size(size)
        mime_type= dir['MimeType']
        if mime_type == 'inode/directory': 
            folder= "📁"
            menu.append([InlineKeyboardButton(f"{folder} {path}", f"leechmenu^{data_callback}^{index}")])
        else:
            menu.append([InlineKeyboardButton(f"[{size}] {path}", f"leechmenu^start_leech_file^{index}")])