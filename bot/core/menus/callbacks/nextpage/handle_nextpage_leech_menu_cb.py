#**************************************************
# Adapted from:
# Source: https://github.com/EvamariaTG/EvaMaria/blob/master/plugins/pm_filter.py
#**************************************************/

from pyrogram.types import InlineKeyboardButton
from bot.core.get_vars import get_val
from pyrogram.types import InlineKeyboardMarkup
from bot.utils.bot_utils.menu_utils import menu_maker_for_rclone, next_page_results

async def next_page_leech(client, callback_query):
    _, next_offset, data_back_cb= callback_query.data.split(" ")
    list_info = get_val("JSON_RESULT_DATA")
    btn= []
    total = len(list_info)
    next_offset = int(next_offset)
    prev_offset = next_offset - 10 

    list_info, _next_offset= next_page_results(list_info, next_offset)
    
    btn.append([InlineKeyboardButton(f" ✅ Select this folder", callback_data= f"leechmenu^start_leech_folder")])
    
    menu_maker_for_rclone(list_info, btn, data_callback="list_dir_leech_menu")

    if next_offset == 0:
        btn.append(
            [InlineKeyboardButton(f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", callback_data="setting pages"),
             InlineKeyboardButton("NEXT ⏩", callback_data= f"n_leech {_next_offset} {data_back_cb}")
            ])
    elif next_offset >= total:
        btn.append(
             [InlineKeyboardButton("⏪ BACK", callback_data=f"n_leech {prev_offset} {data_back_cb}"),
              InlineKeyboardButton(f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}",
                                   callback_data="setting pages")])
    elif next_offset + 10 > total:
        btn.append(
             [InlineKeyboardButton("⏪ BACK", callback_data=f"n_leech {prev_offset} {data_back_cb}"),
              InlineKeyboardButton(f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}",
                                   callback_data="setting pages")])                               
    else:
        btn.append([InlineKeyboardButton("⏪ BACK", callback_data=f"n_leech {prev_offset} {data_back_cb}"),
             InlineKeyboardButton(f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", callback_data="setting pages"),
             InlineKeyboardButton("NEXT ⏩", callback_data=f"n_leech {_next_offset} {data_back_cb}")
            ])

    btn.append(
            [InlineKeyboardButton("⬅️ Back", f"leechmenu^{data_back_cb}")]
        ) 
    btn.append(
            [InlineKeyboardButton("✘ Close Menu", f"leechmenu^selfdest")]
        )

    message= callback_query.message
    default_drive= get_val("DEFAULT_RCLONE_DRIVE")
    base_dir= get_val("BASE_DIR")
    await message.edit(
        f"Select folder or file that you want to leech\n\nPath:`{default_drive}:{base_dir}`", 
        reply_markup= InlineKeyboardMarkup(btn))