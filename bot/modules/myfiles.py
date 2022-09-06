from itertools import pairwise
from os import path as ospath, getcwd
from configparser import ConfigParser
from asyncio.subprocess import PIPE, create_subprocess_exec as exec
from pyrogram.types import InlineKeyboardMarkup
from pyrogram.filters import regex
from pyrogram import filters
from pyrogram.handlers import CallbackQueryHandler, MessageHandler
from bot import Bot
from json import loads as jsonloads
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.filters import CustomFilters
from bot.helper.ext_utils.menu_utils import Menus, rcloneListButtonMaker, rcloneListNextPage
from bot.helper.ext_utils.message_utils import editMessage, sendMarkup, sendMessage
from bot.helper.ext_utils.misc_utils import ButtonMaker, get_rclone_config
from bot.helper.ext_utils.rclone_utils import is_not_config
from bot.helper.ext_utils.var_holder import get_rclone_var, set_rclone_var
from bot.modules.myfiles_settings import calculate_size, delete_selected, delete_selection, myfiles_settings

folder_icon= "📁"

async def handle_myfiles(client, message):
    if await is_not_config(message.from_user.id, message):
        return
    await list_drive(message)

async def list_drive(message, edit=False):
    if message.reply_to_message:
        user_id= message.reply_to_message.from_user.id
    else:
        user_id= message.from_user.id

    buttons = ButtonMaker()

    path= ospath.join(getcwd(), "users", str(user_id), "rclone.conf")
    conf = ConfigParser()
    conf.read(path)

    for j in conf.sections():
        if "team_drive" in list(conf[j]):
            buttons.cb_buildsecbutton(f"{folder_icon} {j}", f"myfilesmenu^drive^{j}^{user_id}")
        else:
            buttons.cb_buildsecbutton(f"{folder_icon} {j}", f"myfilesmenu^drive^{j}^{user_id}")

    for a, b in pairwise(buttons.second_button):
        row= [] 
        if b == None:
            row.append(a)  
            buttons.ap_buildbutton(row)
            break
        row.append(a)
        row.append(b)
        buttons.ap_buildbutton(row)

    buttons.cbl_buildbutton("✘ Close Menu", f"myfilesmenu^close^{user_id}")

    if edit:
        await editMessage("Select your drive to see files", message, reply_markup= InlineKeyboardMarkup(buttons.first_button))
    else:
        await sendMarkup("Select your drive to see files", message, reply_markup= InlineKeyboardMarkup(buttons.first_button))

async def list_dir(message, drive_name, drive_base, back= "back", edit=False):
    user_id= message.reply_to_message.from_user.id
    buttons = ButtonMaker()
    path = get_rclone_config(user_id)
    buttons.cbl_buildbutton(f"⚙️ Folder Settings", f"myfilesmenu^folder_actions^{user_id}")

    cmd = ["rclone", "lsjson", f'--config={path}', f"{drive_name}:{drive_base}" ] 
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
        buttons.cbl_buildbutton("❌Nothing to show❌", f"myfilesmenu^pages^{user_id}")   
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
                menu_type= Menus.MYFILES, 
                callback = "dir",
                user_id= user_id)

        if offset == 0 and total <= 10:
            buttons.cbl_buildbutton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", data="myfilesmenu^pages") 
        else: 
            buttons.dbuildbutton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", "myfilesmenu^pages",
                                    "NEXT ⏩", f"next_myfiles {next_offset} back")   

    buttons.cbl_buildbutton("⬅️ Back", f"myfilesmenu^{back}^{user_id}")
    buttons.cbl_buildbutton("✘ Close Menu", f"myfilesmenu^close^{user_id}")

    msg= f"Your drive files are listed below\n\nPath:`{drive_name}:{drive_base}`"

    if edit:
        await editMessage(msg, message, reply_markup= InlineKeyboardMarkup(buttons.first_button))
    else:
        await sendMarkup(msg, message, reply_markup= InlineKeyboardMarkup(buttons.first_button))

async def myfiles_callback(client, callback_query):
    query= callback_query
    data = query.data
    cmd = data.split("^")
    message = query.message
    user_id= str(query.from_user.id)
    base_dir= get_rclone_var("MYFILES_BASE_DIR", user_id)
    rclone_drive = get_rclone_var("MYFILES_DRIVE", user_id)

    if data == "pages":
        await query.answer()

    if cmd[-1] != user_id:
        return await query.answer("This menu is not for you!", show_alert=True)

    if cmd[1] == "drive":
        await query.answer()     
        #Reset Menu
        set_rclone_var("MYFILES_BASE_DIR", "", user_id)
        base_dir= get_rclone_var("MYFILES_BASE_DIR", user_id)
             
        drive_name= cmd[2]  
        set_rclone_var("MYFILES_DRIVE", drive_name, user_id)
        await list_dir(message, drive_name= drive_name, drive_base=base_dir, edit=True)

    elif cmd[1] == "dir":
        await query.answer()
        path = get_rclone_var(cmd[2], user_id)
        base_dir += path + "/"
        set_rclone_var("MYFILES_BASE_DIR", base_dir, user_id)
        await list_dir(message, drive_name= rclone_drive, drive_base=base_dir, edit=True)

    # Handle back button
    elif cmd[1] == "back":
        await query.answer()
        base_dir_split= base_dir.split("/")[:-2]
        base_dir_string = "" 
        for dir in base_dir_split: 
            base_dir_string += dir + "/"
        base_dir = base_dir_string
        set_rclone_var("MYFILES_BASE_DIR", base_dir, user_id)
        
        if len(base_dir) > 0: 
            await list_dir(message, drive_name= rclone_drive, drive_base=base_dir, edit=True)
        else:
            await list_dir(message, drive_name= rclone_drive, drive_base=base_dir, back= "back_drive", edit=True)     
            
    elif cmd[1] == "back_drive":   
        await query.answer()
        await list_drive(message, edit=True)
    
    #Handle actions
    elif cmd[1] == "file_actions":
        await query.answer()     
        path = get_rclone_var(cmd[2], user_id)
        base_dir += path
        set_rclone_var("MYFILES_BASE_DIR", base_dir, user_id) 
        await myfiles_settings(message, drive_name= rclone_drive, drive_base= base_dir, edit=True, is_folder= False) 

    elif cmd[1] == "folder_actions":
        await query.answer()     
        await myfiles_settings(message, drive_name= rclone_drive, drive_base= base_dir, edit=True, is_folder= True)

    if cmd[1] == "delete_action":
        await query.answer()     
        if cmd[2] == "folder":
            is_folder= True
        elif cmd[2] == "file":
            is_folder= False
        await delete_selection(message, user_id= user_id, is_folder= is_folder)

    elif cmd[1] == "size_action":
        await query.answer()
        await calculate_size(message, drive_base= base_dir, drive_name= rclone_drive, user_id= user_id)

    if cmd[1]== "yes":
        await query.answer()
        if cmd[2] == "folder":
            is_folder= True
        elif cmd[2] == "file":
            is_folder= False
        await delete_selected(message, user_id, drive_base=base_dir , drive_name=rclone_drive, is_folder= is_folder)
        
    elif cmd[1]== "no":
        await query.answer("Closed") 
        await message.delete()
    
    if cmd[1] == "close":
        await query.answer("Closed")
        await message.delete()

async def next_page_myfiles(client, callback_query):
    data= callback_query.data
    message= callback_query.message
    user_id= message.reply_to_message.from_user.id
    _, next_offset, data_back_cb = data.split()
    list_info = get_rclone_var("driveInfo", user_id)
    total = len(list_info)
    next_offset = int(next_offset)
    prev_offset = next_offset - 10 

    buttons = ButtonMaker()
    buttons.cbl_buildbutton(f"⚙️ Folder Settings", f"myfilesmenu^start_folder_actions^{user_id}")

    next_list_info, _next_offset= rcloneListNextPage(list_info, next_offset)

    rcloneListButtonMaker(result_list= next_list_info,
        buttons= buttons,
        menu_type= Menus.MYFILES, 
        callback = "dir",
        user_id= user_id)

    if next_offset == 0:
        buttons.dbuildbutton(f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", "myfilesmenu^pages",
                            "NEXT ⏩", f"next_myfiles {_next_offset} {data_back_cb}")

    elif next_offset >= total:
        buttons.dbuildbutton("⏪ BACK", f"next_myfiles {prev_offset} {data_back_cb}",
                            f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", "myfilesmenu^pages")

    elif next_offset + 10 > total:
        buttons.dbuildbutton("⏪ BACK", f"next_myfiles {prev_offset} {data_back_cb}",
                            f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}","myfilesmenu^pages")                               

    else:
        buttons.tbuildbutton("⏪ BACK", f"next_myfiles {prev_offset} {data_back_cb}",
                            f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", "myfilesmenu^pages",
                            "NEXT ⏩", f"next_myfiles {_next_offset} {data_back_cb}")

    buttons.cbl_buildbutton("⬅️ Back", f"myfilesmenu^{data_back_cb}^{user_id}")
    buttons.cbl_buildbutton("✘ Close Menu", f"myfilesmenu^close^{user_id}")

    myfiles_drive= get_rclone_var("MYFILES_DRIVE", user_id)
    base_dir= get_rclone_var("MYFILES_BASE_DIR", user_id)
    await editMessage(f"Your drive files are listed below\n\nPath:`{myfiles_drive}:{base_dir}`", message, 
                      reply_markup= InlineKeyboardMarkup(buttons.first_button))


next_page_myfiles_cb= CallbackQueryHandler( next_page_myfiles, filters= regex("next_myfiles"))
myfiles_cb = CallbackQueryHandler(myfiles_callback, filters= regex("myfilesmenu"))
myfiles_handler = MessageHandler(handle_myfiles, filters= filters.command(BotCommands.MyFilesCommand) & CustomFilters.user_filter | CustomFilters.chat_filter)

Bot.add_handler(myfiles_cb)
Bot.add_handler(next_page_myfiles_cb)
Bot.add_handler(myfiles_handler)