#**************************************************
# Adapted from:
# Source: https://github.com/EvamariaTG/EvaMaria/blob/master/plugins/pm_filter.py
#**************************************************/

from bot.core.get_vars import get_val
from telethon.tl.types import KeyboardButtonCallback
from telethon.errors.rpcerrorlist import MessageNotModifiedError
from bot.core.menus.menu_mirrorset import get_list_drive_results_mirrorset, list_drive_mirrorset


async def next_page_mirrorset(callback_query):
    _, offset, data_back_cb = callback_query.data.decode().split(" ")
    data = get_val("JSON_RESULT_DATA")
    btn= []
    offset = int(offset)
    
    result, next_offset, total = get_list_drive_results_mirrorset(data, offset=offset)

    btn.append(
        [KeyboardButtonCallback(f" ✅ Select this folder", f"mirrorsetmenu^selfdest")]
        )

    list_drive_mirrorset(result, menu=btn, data_cb= "list_dir_mirrorset_menu")
        
    n_offset = int(next_offset)
    off_set = offset - 10 

    if offset == 0:
        btn.append(
            [KeyboardButtonCallback(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", data="setting pages"),
             KeyboardButtonCallback("NEXT ⏩", data= f"n_mirrorset {n_offset} {data_back_cb}")
            ])

    elif offset >= total:
        btn.append(
             [KeyboardButtonCallback("⏪ BACK", data=f"n_mirrorset {off_set} {data_back_cb}"),
              KeyboardButtonCallback(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}",
                                   data="setting pages")])

    elif offset + 10 > total:
        btn.append(
             [KeyboardButtonCallback("⏪ BACK", data=f"n_mirrorset {off_set} {data_back_cb}"),
              KeyboardButtonCallback(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}",
                                   data="setting pages")])                               

    else:
        btn.append([KeyboardButtonCallback("⏪ BACK", data=f"n_mirrorset {off_set} {data_back_cb}"),
             KeyboardButtonCallback(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", data="setting pages"),
             KeyboardButtonCallback("NEXT ⏩", data=f"n_mirrorset {n_offset} {data_back_cb}")
            ])

    btn.append(
            [KeyboardButtonCallback("⬅️ Back", f"mirrorsetmenu^{data_back_cb}")]
        )
    
    btn.append(
            [KeyboardButtonCallback("✘ Close Menu", f"mirrorsetmenu^selfdest")]
        )

    try:
        mmes= await callback_query.get_message()
        d_rclone_drive= get_val("DEFAULT_RCLONE_DRIVE")
        base_dir= get_val("BASE_DIR")
        await mmes.edit(f"Select folder where you want to store files\n\nPath:`{d_rclone_drive}:{base_dir}`", buttons=btn)
    except MessageNotModifiedError:
        pass