#**************************************************
# Adapted from:
# Source: https://github.com/EvamariaTG/EvaMaria/blob/master/plugins/pm_filter.py
#**************************************************/

from pyrogram.types import InlineKeyboardMarkup
from bot.core.varholderwrap import get_val
from bot.utils.bot_utils.menu_utils import Menus, rcloneListButtonMaker, rcloneListNextPage
from bot.utils.bot_utils.message_utils import editMessage
from bot.utils.bot_utils.misc_utils import ButtonMaker


async def next_page_myfiles(client, callback_query):
    data= callback_query.data
    message= callback_query.message
    _, next_offset, data_back_cb = data.split()
    list_info = get_val("list_info")
    total = len(list_info)
    next_offset = int(next_offset)
    prev_offset = next_offset - 10 

    buttons = ButtonMaker()
    buttons.cbl_buildbutton(f"⚙️ Folder Settings", f"myfilesmenu^start_folder_actions")

    next_list_info, _next_offset= rcloneListNextPage(list_info, next_offset)

    rcloneListButtonMaker(result_list= next_list_info,
        buttons=buttons,
        menu_type= Menus.MYFILES, 
        callback = "list_dir_myfiles_menu")

    if next_offset == 0:
        buttons.dbuildbutton(f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", "myfilesmenu^pages",
                            "NEXT ⏩", f"n_myfiles {_next_offset} {data_back_cb}")

    elif next_offset >= total:
        buttons.dbuildbutton("⏪ BACK", f"n_myfiles {prev_offset} {data_back_cb}",
                            f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", "myfilesmenu^pages")

    elif next_offset + 10 > total:
        buttons.dbuildbutton("⏪ BACK", f"n_myfiles {prev_offset} {data_back_cb}",
                            f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}","myfilesmenu^pages")                               

    else:
        buttons.tbuildbutton("⏪ BACK", f"n_myfiles {prev_offset} {data_back_cb}",
                            f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", "myfilesmenu^pages",
                            "NEXT ⏩", f"n_myfiles {_next_offset} {data_back_cb}")

    buttons.cbl_buildbutton("⬅️ Back", f"myfilesmenu^{data_back_cb}")
    buttons.cbl_buildbutton("✘ Close Menu", f"myfilesmenu^close")

    default_drive= get_val("RCLONE_DRIVE")
    base_dir= get_val("MYFILES_BASE_DIR")
    await editMessage(f"Your drive files are listed below\n\nPath:`{default_drive}:{base_dir}`", message, 
                      reply_markup= InlineKeyboardMarkup(buttons.first_button))