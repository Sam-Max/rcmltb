#**************************************************
# Adapted from:
# Source: https://github.com/EvamariaTG/EvaMaria/blob/master/plugins/pm_filter.py
#**************************************************/

import logging 
from bot.core.get_vars import get_val
from telethon.tl.types import KeyboardButtonCallback
from telethon.errors.rpcerrorlist import MessageNotModifiedError
from bot.core.menus.main_menu import get_list_drive_results_main, list_drive_main


botlog = logging.getLogger(__name__)

async def next_page_menu(callback_query):
    _, offset, data_back_cb = callback_query.data.decode().split(" ")
    data = get_val("JSON_RESULT_DATA")
    btn= []
    offset = int(offset)
    
    result, next_offset, total = await get_list_drive_results_main(data, offset=offset)

    btn.append(
        [KeyboardButtonCallback(f" ✅ Select this folder", f"mainmenu^selfdest")]
        )

    list_drive_main(result, menu=btn, data_cb= "list_dir_main_menu")
        
    n_offset = int(next_offset)
    off_set = offset - 10 

    if offset == 0:
        btn.append(
            [KeyboardButtonCallback(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", data="setting pages"),
             KeyboardButtonCallback("NEXT ⏩", data= f"next {n_offset} {data_back_cb}")
            ])

    elif offset >= total:
        btn.append(
             [KeyboardButtonCallback("⏪ BACK", data=f"next {off_set} {data_back_cb}"),
              KeyboardButtonCallback(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}",
                                   data="setting pages")])

    elif offset + 10 > total:
        btn.append(
             [KeyboardButtonCallback("⏪ BACK", data=f"next {off_set} {data_back_cb}"),
              KeyboardButtonCallback(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}",
                                   data="setting pages")])                               

    else:
        btn.append([KeyboardButtonCallback("⏪ BACK", data=f"next {off_set} {data_back_cb}"),
             KeyboardButtonCallback(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", data="setting pages"),
             KeyboardButtonCallback("NEXT ⏩", data=f"next {n_offset} {data_back_cb}")
            ])

    btn.append(
            [KeyboardButtonCallback("⬅️ Back", f"mainmenu^{data_back_cb}")]
        )
    
    btn.append(
            [KeyboardButtonCallback("✘ Close Menu", f"mainmenu^selfdest")]
        )

    try:
        mmes= await callback_query.get_message()
        d_rclone_drive= get_val("DEF_RCLONE_DRIVE")
        base_dir= get_val("BASE_DIR")
        await mmes.edit(f"Select folder where you want to store files\n\nPath:`{d_rclone_drive}:{base_dir}`", buttons=btn)
    except MessageNotModifiedError:
        pass