import logging as log
from bot.core.get_vars import get_val
from telethon.tl.types import KeyboardButtonCallback
from telethon.errors.rpcerrorlist import MessageNotModifiedError

from bot.utils.list_selected_drive_copy_menu import get_list_drive_results_copy, list_drive_copy

async def next_page_copy(callback_query):
    _, offset, is_dest_drive = callback_query.data.decode().split(" ")
    log.info(f"NEXT_OFFSET: {offset}")
    data = get_val("JSON_RESULT_DATA")
    btn= []
    offset = int(offset)
    
    result, next_offset, total = await get_list_drive_results_copy(data, offset=offset)

    if is_dest_drive:
         btn.append([KeyboardButtonCallback(f" ✅ Seleccione esta Carpeta", f"copymenu^start_copy_cb")])
    else:
         btn.append([KeyboardButtonCallback(f" ✅ Seleccione esta Carpeta", f"copymenu^rclone_menu_copy_cb")])
    
    list_drive_copy(result= result, callback="list_dir_origin", menu=btn)
        
    n_offset = int(next_offset)
    off_set = offset - 10 

    if offset == 0:
        btn.append(
            [KeyboardButtonCallback(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", data="setting pages"),
             KeyboardButtonCallback("NEXT ⏩", data= f"next_copy {next_offset}".encode("UTF-8"))
            ])

    elif offset + 10 >= total:
        btn.append(
             [KeyboardButtonCallback("⏪ BACK", data=f"next_copy {off_set}"),
              KeyboardButtonCallback(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}",
                                   data="setting pages")])
    else:
        btn.append([KeyboardButtonCallback("⏪ BACK", data=f"next_copy {off_set}"),
             KeyboardButtonCallback(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", data="setting pages"),
             KeyboardButtonCallback("NEXT ⏩", data=f"next_copy {n_offset}")
            ])
    try:
        mmes= await callback_query.get_message()
        d_rclone_drive= get_val("ORIGIN_DRIVE")
        base_dir= get_val("BASE_DIR_COPY")
        await mmes.edit(f"Ruta:`{d_rclone_drive}:{base_dir}`", buttons=btn)
    except MessageNotModifiedError as e:
        log.info(e)
        pass