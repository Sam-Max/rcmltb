from asyncio.subprocess import PIPE, create_subprocess_exec as exec
from os import path as ospath, getcwd
from configparser import ConfigParser
from bot import Bot
from json import loads as jsonloads
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.filters import CustomFilters
from bot.helper.ext_utils.menu_utils import Menus, rcloneListButtonMaker, rcloneListNextPage
from bot.helper.ext_utils.message_utils import editMessage, sendMarkup, sendMessage
from bot.helper.ext_utils.misc_utils import ButtonMaker, get_rclone_config, pairwise
from bot.helper.ext_utils.rclone_utils import is_not_config
from bot.helper.ext_utils.var_holder import get_rclone_var, set_rclone_var
from pyrogram.filters import regex
from pyrogram import filters
from pyrogram.handlers import CallbackQueryHandler, MessageHandler
from pyrogram.types import InlineKeyboardMarkup

yes = "✅"
folder_icon= "📁"

async def handle_mirrorset(client, message):
    user_id= message.from_user.id
    if await is_not_config(user_id, message):
        return
    rclone_drive = get_rclone_var("MIRRORSET_DRIVE", user_id)              
    base_dir= get_rclone_var("MIRRORSET_BASE_DIR", user_id)
    await list_drive(message, rclone_drive, base_dir)     

async def list_drive(message, rclone_drive="", base_dir="", edit=False):
    if message.reply_to_message:
        user_id= message.reply_to_message.from_user.id
    else:
        user_id= message.from_user.id

    buttons = ButtonMaker()

    path= ospath.join(getcwd(), "users", str(user_id), "rclone.conf")
    conf = ConfigParser()
    conf.read(path)

    for drive in conf.sections():
        prev = ""
        if drive == get_rclone_var(f"MIRRORSET_DRIVE", user_id):
            prev = yes
        if "team_drive" in list(conf[drive]):
            buttons.cb_buildsecbutton(f"{prev} {folder_icon} {drive}", f"mirrorsetmenu^drive^{drive}^{user_id}")
        else:
            buttons.cb_buildsecbutton(f"{prev} {folder_icon} {drive}", f"mirrorsetmenu^drive^{drive}^{user_id}")

    for a, b in pairwise(buttons.second_button):
        row= [] 
        if b == None:
            row.append(a)  
            buttons.ap_buildbutton(row)
            break
        row.append(a)
        row.append(b)
        buttons.ap_buildbutton(row)

    buttons.cbl_buildbutton("✘ Close Menu", f"mirrorsetmenu^close^{user_id}")

    msg= f"Select cloud where you want to upload file\n\nPath:`{rclone_drive}:{base_dir}`" 

    if edit:
        await editMessage(msg, message, reply_markup= InlineKeyboardMarkup(buttons.first_button))
    else:
        await sendMarkup(msg, message, reply_markup= InlineKeyboardMarkup(buttons.first_button))

async def list_dir(message, drive_name, drive_base, back= "back", edit=False):
    user_id= message.reply_to_message.from_user.id
    buttons = ButtonMaker()
    path = get_rclone_config(user_id)
    buttons.cbl_buildbutton(f"✅ Select this folder", f"mirrorsetmenu^close^{user_id}")

    cmd = ["rclone", "lsjson", '--dirs-only', f'--config={path}', f"{drive_name}:{drive_base}" ] 
    process = await exec(*cmd, stdout=PIPE, stderr=PIPE)
    out, err = await process.communicate()
    out = out.decode().strip()
    return_code = await process.wait()

    if return_code != 0:
        err = err.decode().strip()
        return await sendMessage(f'Error: {err}', message)

    list_info = jsonloads(out)
    list_info.sort(key=lambda x: x["Size"])
    set_rclone_var("driveInfo", list_info, user_id)

    if len(list_info) == 0:
        buttons.cbl_buildbutton("❌Nothing to show❌", "mirrorsetmenu^pages^{user_id}")
    else:
        total = len(list_info)
        max_results= 10
        offset= 0
        start = offset
        end = max_results + start
        next_offset = offset + max_results

        if end > total:
            list_info= list_info[offset:]    
        elif offset >= total:
            list_info= []    
        else:
            list_info= list_info[start:end]       
        
        rcloneListButtonMaker(result_list= list_info,
                buttons=buttons,
                menu_type= Menus.MIRRORSET, 
                callback = "dir",
                user_id= user_id)

        if offset == 0 and total <= 10:
            buttons.cbl_buildbutton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", f"mirrorsetmenu^pages^{user_id}") 
        else:
            buttons.dbuildbutton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", f"mirrorsetmenu^pages^{user_id}",
                                "NEXT ⏩", f"next_mirrorset {next_offset} {back}")

    buttons.cbl_buildbutton("⬅️ Back", f"mirrorsetmenu^{back}^{user_id}")
    buttons.cbl_buildbutton("✘ Close Menu", f"mirrorsetmenu^close^{user_id}")

    msg= f"Select folder where you want to store files\n\nPath:`{drive_name}:{drive_base}`"

    if edit:
        await editMessage(msg, message, reply_markup= InlineKeyboardMarkup(buttons.first_button))
    else:
        await sendMarkup(msg, message, reply_markup= InlineKeyboardMarkup(buttons.first_button))

async def mirrorset_callback(client, callback_query):
    query= callback_query
    data = query.data
    cmd = data.split("^")
    message = query.message
    user_id= query.from_user.id
    base_dir= get_rclone_var("MIRRORSET_BASE_DIR", user_id)
    rclone_drive = get_rclone_var("MIRRORSET_DRIVE", user_id)

    if cmd[1] == "pages":
        return await query.answer()

    if int(cmd[-1]) != user_id:
        return await query.answer("This menu is not for you!", alert=True)
        
    elif cmd[1] == "drive":
        #Reset Menu
        set_rclone_var("MIRRORSET_BASE_DIR", "", user_id)
        base_dir= get_rclone_var("MIRRORSET_BASE_DIR", user_id)

        drive_name= cmd[2]
        set_rclone_var("MIRRORSET_DRIVE", drive_name, user_id)
        await list_dir(message, drive_name= drive_name, drive_base=base_dir, edit=True)
        await query.answer()

    elif cmd[1] == "dir":
        path = get_rclone_var(cmd[2], user_id)
        base_dir += path + "/"
        set_rclone_var("MIRRORSET_BASE_DIR", base_dir, user_id)
        await list_dir(message, drive_name= rclone_drive, drive_base=base_dir, edit=True)
        await query.answer()

    elif cmd[1] == "back":
        base_dir_split= base_dir.split("/")[:-2]
        base_dir_string = "" 
        for dir in base_dir_split: 
            base_dir_string += dir + "/"
        base_dir = base_dir_string
        set_rclone_var("MIRRORSET_BASE_DIR", base_dir, user_id)

        if len(base_dir) > 0: 
            await list_dir(message, drive_name= rclone_drive, drive_base=base_dir, edit=True)
        else:
            await list_dir(message, drive_name= rclone_drive, drive_base=base_dir, back= "back_drive", edit=True)     
        await query.answer() 

    elif cmd[1] == "back_drive":   
        await list_drive(message, edit=True)
        await query.answer()
        
    elif cmd[1] == "close":
        await query.answer("Closed")
        await message.delete()

async def next_page_mirrorset(client, callback_query):
    data= callback_query.data
    message= callback_query.message
    user_id= message.reply_to_message.from_user.id
    _, next_offset, data_back_cb = data.split()
    list_info = get_rclone_var("driveInfo", user_id)
    total = len(list_info)
    next_offset = int(next_offset)
    prev_offset = next_offset - 10 

    buttons = ButtonMaker()
    buttons.cbl_buildbutton("✅ Select this folder", f"mirrorsetmenu^close^{user_id}")

    next_list_info, _next_offset= rcloneListNextPage(list_info, next_offset) 
    rcloneListButtonMaker(result_list= next_list_info, 
            buttons= buttons,
            menu_type= Menus.MIRRORSET,
            callback= "dir",
            user_id= user_id)

    if next_offset == 0:
        buttons.dbuildbutton(f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", "mirrorsetmenu^pages",
                            "NEXT ⏩", f"next_mirrorset {_next_offset} {data_back_cb}")

    elif next_offset >= total:
        buttons.dbuildbutton("⏪ BACK", f"next_mirrorset {prev_offset} {data_back_cb}",
                            f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", "mirrorsetmenu^pages")

    elif next_offset + 10 > total:
        buttons.dbuildbutton("⏪ BACK", f"next_mirrorset {prev_offset} {data_back_cb}",
                             f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", "mirrorsetmenu^pages")                              

    else:
        buttons.tbuildbutton("⏪ BACK", f"next_mirrorset {prev_offset} {data_back_cb}",
                            f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", "mirrorsetmenu^pages",
                            "NEXT ⏩", f"next_mirrorset {_next_offset} {data_back_cb}")

    buttons.cbl_buildbutton("⬅️ Back", f"mirrorsetmenu^{data_back_cb}^{user_id}")
    buttons.cbl_buildbutton("✘ Close Menu", f"mirrorsetmenu^close^{user_id}")

    mirrorset_drive= get_rclone_var("MIRRORSET_DRIVE", user_id)
    base_dir= get_rclone_var("MIRRORSET_BASE_DIR", user_id)
    await message.edit(f"Select folder where you want to store files\n\nPath:`{mirrorset_drive}:{base_dir}`", reply_markup= InlineKeyboardMarkup(buttons.first_button))

 
next_mirrorset_cb= CallbackQueryHandler(next_page_mirrorset, filters= regex("next_mirrorset"))
mirrorset_cb = CallbackQueryHandler(mirrorset_callback, filters= regex("mirrorsetmenu"))
mirrorset_handler = MessageHandler(handle_mirrorset, filters= filters.command(BotCommands.MirrorSetCommand) & CustomFilters.user_filter | CustomFilters.chat_filter)

Bot.add_handler(mirrorset_cb)
Bot.add_handler(next_mirrorset_cb)
Bot.add_handler(mirrorset_handler)