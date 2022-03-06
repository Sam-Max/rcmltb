#**************************************************
# Based on:
# Source: https://github.com/EvamariaTG/EvaMaria/blob/master/plugins/pm_filter.py
#**************************************************/

import logging as log
from pyrogram.types import InlineKeyboardButton
from bot.core.get_vars import get_val
from telethon.errors.rpcerrorlist import MessageNotModifiedError
from pyrogram.types import InlineKeyboardMarkup
from bot.utils.list_selected_drive_copy_menu import get_list_drive_results_copy, list_drive_copy
from bot.utils.list_selected_drive_leech_menu import list_drive_leech

async def next_page_leech(client, callback_query):
    _, offset= callback_query.data.split(" ")
    log.info(f"NEXT_OFFSET: {offset}")
    data = get_val("JSON_RESULT_DATA")
    btn= []
    offset = int(offset)
    
    result, next_offset, total = await get_list_drive_results_copy(data, offset=offset)

    list_drive_leech(result= result, data_cb="list_dir_leech_menu", menu=btn)
        
    n_offset = int(next_offset)
    off_set = offset - 10 

    if offset == 0:
        btn.append(
            [InlineKeyboardButton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", callback_data="setting pages"),
             InlineKeyboardButton("NEXT ⏩", callback_data= f"n_leech {n_offset}".encode("UTF-8"))
            ])

    elif offset >= total:
        btn.append(
             [InlineKeyboardButton("⏪ BACK", callback_data=f"n_leech {off_set}"),
              InlineKeyboardButton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}",
                                   callback_data="setting pages")])

    elif offset + 10 > total:
        btn.append(
             [InlineKeyboardButton("⏪ BACK", callback_data=f"n_leech {off_set}"),
              InlineKeyboardButton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}",
                                   callback_data="setting pages")])                               

    else:
        btn.append([InlineKeyboardButton("⏪ BACK", callback_data=f"n_leech {off_set}"),
             InlineKeyboardButton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", callback_data="setting pages"),
             InlineKeyboardButton("NEXT ⏩", callback_data=f"n_leech {n_offset}")
            ])


    btn.append(
            [InlineKeyboardButton("Close Menu", f"mainmenu^selfdest")]
        )
                
    try:
        mmes= callback_query.message
        def_rc_drive= get_val("DEF_RCLONE_DRIVE")
        base_dir= get_val("BASE_DIR")
        await mmes.edit(f"Select folder or file to leech\n\nPath:`{def_rc_drive}:{base_dir}`", reply_markup= InlineKeyboardMarkup(btn))
    except MessageNotModifiedError:
        pass