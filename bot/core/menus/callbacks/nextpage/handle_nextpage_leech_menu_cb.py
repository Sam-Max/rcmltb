#**************************************************
# Adapted from:
# Source: https://github.com/EvamariaTG/EvaMaria/blob/master/plugins/pm_filter.py
#**************************************************/

from pyrogram.types import InlineKeyboardButton
from bot.core.get_vars import get_val
from telethon.errors.rpcerrorlist import MessageNotModifiedError
from pyrogram.types import InlineKeyboardMarkup
from bot.core.menus.menu_leech import get_list_drive_results_leech, list_drive_leech


async def next_page_leech(client, callback_query):
    _, offset, data_back_cb= callback_query.data.split(" ")
    data = get_val("JSON_RESULT_DATA")
    btn= []
    offset = int(offset)
    
    result, next_offset, total = await get_list_drive_results_leech(data, offset=offset)

    btn.append(
        [InlineKeyboardButton(f" ✅ Select this folder", callback_data= f"leechmenu^start_leech_folder")]
        )

    list_drive_leech(result= result, data_cb="list_dir_leech_menu", menu=btn)
        
    n_offset = int(next_offset)
    off_set = offset - 10 

    if offset == 0:
        btn.append(
            [InlineKeyboardButton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", callback_data="setting pages"),
             InlineKeyboardButton("NEXT ⏩", callback_data= f"n_leech {n_offset} {data_back_cb}")
            ])

    elif offset >= total:
        btn.append(
             [InlineKeyboardButton("⏪ BACK", callback_data=f"n_leech {off_set} {data_back_cb}"),
              InlineKeyboardButton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}",
                                   callback_data="setting pages")])

    elif offset + 10 > total:
        btn.append(
             [InlineKeyboardButton("⏪ BACK", callback_data=f"n_leech {off_set} {data_back_cb}"),
              InlineKeyboardButton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}",
                                   callback_data="setting pages")])                               

    else:
        btn.append([InlineKeyboardButton("⏪ BACK", callback_data=f"n_leech {off_set} {data_back_cb}"),
             InlineKeyboardButton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", callback_data="setting pages"),
             InlineKeyboardButton("NEXT ⏩", callback_data=f"n_leech {n_offset} {data_back_cb}")
            ])


    btn.append(
            [InlineKeyboardButton("⬅️ Back", f"leechmenu^{data_back_cb}")]
        ) 

    btn.append(
            [InlineKeyboardButton("✘ Close Menu", f"leechmenu^selfdest")]
        )
                
    try:
        mmes= callback_query.message
        def_rc_drive= get_val("DEF_RCLONE_DRIVE")
        base_dir= get_val("BASE_DIR")
        await mmes.edit(f"Select folder or file that you want to leech\n\nPath:`{def_rc_drive}:{base_dir}`", reply_markup= InlineKeyboardMarkup(btn))
    except MessageNotModifiedError:
        pass