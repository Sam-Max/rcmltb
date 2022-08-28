#**************************************************
# Adapted from:
# Source: https://github.com/EvamariaTG/EvaMaria/blob/master/plugins/pm_filter.py
#**************************************************/

from bot import LOGGER
from bot.core.varholderwrap import get_val
from bot.utils.bot_utils.menu_utils import Menus, rcloneListButtonMaker, rcloneListNextPage
from bot.utils.bot_utils.misc_utils import TelethonButtonMaker


async def next_page_copy(callback_query):
    data= callback_query.data
    message= await callback_query.get_message()
    _, next_offset, is_second_menu, data_back_cb = data.decode().split()
    list_info = get_val("list_info")
    total = len(list_info)
    next_offset = int(next_offset)
    prev_offset = next_offset - 10 
    
    buttons = TelethonButtonMaker()
    next_list_info, _next_offset= rcloneListNextPage(list_info, next_offset) 

    if is_second_menu:
        buttons.cbl_buildbutton("✅ Select this folder", "copymenu^start_copy")
    else:
        buttons.cbl_buildbutton("✅ Select this folder", "copymenu^rclone_menu_copy^_^False")
    
    if is_second_menu:
        rcloneListButtonMaker(result_list= next_list_info, 
            buttons= buttons,
            menu_type= Menus.COPY,
            callback="list_dir_dest")
    else:
        rcloneListButtonMaker(result_list= next_list_info, 
            buttons= buttons,
            menu_type= Menus.COPY,
            callback="list_dir_origin")

    if next_offset == 0:
        buttons.dbuildbutton(f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", "setting pages",
                            "NEXT ⏩", f"n_copy {_next_offset} {is_second_menu} {data_back_cb}")
    
    elif next_offset >= total:
        buttons.dbuildbutton("⏪ BACK", f"n_copy {prev_offset} {is_second_menu} {data_back_cb}",
                            f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}",
                                   "setting pages")

    elif next_offset + 10 > total:
        buttons.dbuildbutton("⏪ BACK", f"n_copy {prev_offset} {is_second_menu} {data_back_cb}",
                            f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}","setting pages")                               
    else:
        buttons.tbuildbutton("⏪ BACK", f"n_copy {prev_offset} {is_second_menu} {data_back_cb}",
                            f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", "setting pages",
                            "NEXT ⏩", f"n_copy {_next_offset} {is_second_menu} {data_back_cb}")

    buttons.cbl_buildbutton("⬅️ Back", f"copymenu^{data_back_cb}")
    buttons.cbl_buildbutton("✘ Close Menu", f"copymenu^selfdest")
                            
    try:
        if is_second_menu:
            dest_drive= get_val("DESTINATION_DRIVE")
            dest_dir= get_val("DESTINATION_DIR")
            await message.edit(f"Select folder where you want to copy\n\nPath:`{dest_drive}:{dest_dir}`", buttons=buttons.first_button)
        else:
            origin_drive= get_val("ORIGIN_DRIVE")
            origin_dir= get_val("ORIGIN_DIR")
            await message.edit(f"Select file or folder which you want to copy\n\nPath:`{origin_drive}:{origin_dir}`", buttons=buttons.first_button)
    except:
        pass