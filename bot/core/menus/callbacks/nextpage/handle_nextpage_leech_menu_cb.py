#**************************************************
# Adapted from:
# Source: https://github.com/EvamariaTG/EvaMaria/blob/master/plugins/pm_filter.py
#**************************************************/

from pyrogram.types import InlineKeyboardMarkup
from bot.core.varholderwrap import get_val
from bot.utils.bot_utils.menu_utils import Menus, rcloneListButtonMaker, rcloneListNextPage
from bot.utils.bot_utils.message_utils import editMessage
from bot.utils.bot_utils.misc_utils import ButtonMaker


async def next_page_leech(client, callback_query):
    data = callback_query.data
    message= callback_query.message
    _, next_offset, data_back_cb= data.split()
    list_info = get_val("list_info")
    total = len(list_info)
    next_offset = int(next_offset)
    prev_offset = next_offset - 10 

    buttons = ButtonMaker()
    buttons.cbl_buildbutton(f"✅ Select this folder", data= f"leechmenu^start_leech_folder")

    next_list_info, _next_offset= rcloneListNextPage(list_info, next_offset)

    rcloneListButtonMaker(result_list= next_list_info,
        buttons=buttons,
        menu_type= Menus.LEECH, 
        callback = "list_dir_leech_menu")

    if next_offset == 0:
        buttons.dbuildbutton(first_text = f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", first_callback="setting pages", 
                            second_text= "NEXT ⏩", second_callback= f"n_leech {_next_offset} {data_back_cb}" )
    
    elif next_offset >= total:
        buttons.dbuildbutton(first_text="⏪ BACK", first_callback= f"n_leech {prev_offset} {data_back_cb}", 
                        second_text=f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", second_callback="setting pages")
   
    elif next_offset + 10 > total:
        buttons.dbuildbutton(first_text="⏪ BACK", first_callback= f"n_leech {prev_offset} {data_back_cb}", 
                        second_text= f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", second_callback="setting pages")                               
    else:
        buttons.tbuildbutton(first_text="⏪ BACK", first_callback= f"n_leech {prev_offset} {data_back_cb}", 
                            second_text= f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", second_callback="setting pages",
                            third_text="NEXT ⏩", third_callback=f"n_leech {_next_offset} {data_back_cb}")

    buttons.cbl_buildbutton("⬅️ Back", f"leechmenu^{data_back_cb}")
    buttons.cbl_buildbutton("✘ Close Menu", f"leechmenu^selfdest")

    default_drive= get_val("RCLONE_DRIVE")
    base_dir= get_val("LEECH_BASE_DIR")
    await editMessage(f"Select folder or file that you want to leech\n\nPath:`{default_drive}:{base_dir}`", message, 
                        reply_markup= InlineKeyboardMarkup(buttons.first_button))