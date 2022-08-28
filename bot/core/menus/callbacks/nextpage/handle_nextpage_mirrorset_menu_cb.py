#**************************************************
# Adapted from:
# Source: https://github.com/EvamariaTG/EvaMaria/blob/master/plugins/pm_filter.py
#**************************************************/

from bot.core.varholderwrap import get_val
from bot.utils.bot_utils.menu_utils import Menus, rcloneListButtonMaker, rcloneListNextPage
from bot.utils.bot_utils.misc_utils import TelethonButtonMaker


async def next_page_mirrorset(callback_query):
    data= callback_query.data
    message= await callback_query.get_message()
    _, next_offset, data_back_cb = data.decode().split()
    list_info = get_val("list_info")
    total = len(list_info)
    next_offset = int(next_offset)
    prev_offset = next_offset - 10 

    buttons = TelethonButtonMaker()
    buttons.cbl_buildbutton("✅ Select this folder", f"mirrorsetmenu^selfdest")

    next_list_info, _next_offset= rcloneListNextPage(list_info, next_offset) 
    rcloneListButtonMaker(result_list= next_list_info, 
            buttons= buttons,
            menu_type= Menus.MIRRORSET,
            callback="list_dir_mirrorset_menu")

    if next_offset == 0:
        buttons.dbuildbutton(f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", "setting pages",
                            "NEXT ⏩", f"n_mirrorset {_next_offset} {data_back_cb}")

    elif next_offset >= total:
        buttons.dbuildbutton("⏪ BACK", f"n_mirrorset {prev_offset} {data_back_cb}",
                            f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", "setting pages")

    elif next_offset + 10 > total:
        buttons.dbuildbutton("⏪ BACK", f"n_mirrorset {prev_offset} {data_back_cb}",
                             f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", "setting pages")                              

    else:
        buttons.tbuildbutton("⏪ BACK", f"n_mirrorset {prev_offset} {data_back_cb}",
                            f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", "setting pages",
                            "NEXT ⏩", f"n_mirrorset {_next_offset} {data_back_cb}")

    buttons.cbl_buildbutton("⬅️ Back", f"mirrorsetmenu^{data_back_cb}")
    buttons.cbl_buildbutton("✘ Close Menu", f"mirrorsetmenu^close")

    d_rclone_drive= get_val("RCLONE_MIRRORSET_DRIVE")
    base_dir= get_val("MIRRORSET_BASE_DIR")
    await message.edit(f"Select folder where you want to store files\n\nPath:`{d_rclone_drive}:{base_dir}`", buttons=buttons.first_button)