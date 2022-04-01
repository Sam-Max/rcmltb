#**************************************************
# Adapted from:
# Source: https://github.com/EvamariaTG/EvaMaria/blob/master/plugins/pm_filter.py
#**************************************************/

from bot.core.get_vars import get_val
from telethon.tl.types import KeyboardButtonCallback
from telethon.errors.rpcerrorlist import MessageNotModifiedError
from bot.core.menus.menu_copy import get_list_drive_results_copy, list_drive_copy


async def next_page_copy(callback_query):
    _, offset, is_second_menu, data_back_cb = callback_query.data.decode().split(" ")
    data = get_val("JSON_RESULT_DATA")
    btn= []
    offset = int(offset)
    
    result, next_offset, total = await get_list_drive_results_copy(data, offset=offset)

    if is_second_menu == "True":
        btn.append([KeyboardButtonCallback(f" ✅ Select this folder", f"copymenu^start_copy")])
    else:
        btn.append([KeyboardButtonCallback(f" ✅ Select this folder", f"copymenu^rclone_menu_copy^_^False")])
    
    if is_second_menu == "True":
        list_drive_copy(result= result, callback="list_dir_dest", menu=btn)
    else:
        list_drive_copy(result= result, callback="list_dir_origin", menu=btn)
        
    n_offset = int(next_offset)
    off_set = offset - 10 

    if offset == 0:
             btn.append(
            [KeyboardButtonCallback(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", data="setting pages"),
             KeyboardButtonCallback("NEXT ⏩", data= f"n_copy {n_offset} {is_second_menu} {data_back_cb}".encode("UTF-8"))
            ])

    elif offset >= total:
        btn.append(
             [KeyboardButtonCallback("⏪ BACK", data=f"n_copy {off_set} {is_second_menu} {data_back_cb}"),
              KeyboardButtonCallback(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}",
                                   data="setting pages")])

    elif offset + 10 > total:
        btn.append(
             [KeyboardButtonCallback("⏪ BACK", data=f"n_copy {off_set} {is_second_menu} {data_back_cb}"),
              KeyboardButtonCallback(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}",
                                   data="setting pages")])                               

    else:
        btn.append([KeyboardButtonCallback("⏪ BACK", data=f"n_copy {off_set} {is_second_menu} {data_back_cb}"),
             KeyboardButtonCallback(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", data="setting pages"),
             KeyboardButtonCallback("NEXT ⏩", data=f"n_copy {n_offset} {is_second_menu} {data_back_cb}")
            ])

    btn.append(
            [KeyboardButtonCallback("⬅️ Back", f"copymenu^{data_back_cb}")]
        )

    btn.append(
            [KeyboardButtonCallback("✘ Close Menu", f"copymenu^selfdest")]
        )
                            
    try:
        mmes= await callback_query.get_message()
        if is_second_menu == "True":
             dest_drive= get_val("DEST_DRIVE")
             dest_dir= get_val("DEST_DIR")
             await mmes.edit(f"Select folder where you want to copy\n\nPath:`{dest_drive}:{dest_dir}`", buttons=btn)
        else:
            origin_drive= get_val("ORIGIN_DRIVE")
            origin_dir= get_val("ORIGIN_DIR")
            await mmes.edit(f"Select file or folder which you want to copy\n\nPath:`{origin_drive}:{origin_dir}`", buttons=btn)
    except MessageNotModifiedError:
        pass