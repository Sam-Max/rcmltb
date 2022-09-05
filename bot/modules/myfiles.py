from itertools import pairwise
from os import path as ospath, getcwd
from configparser import ConfigParser
from pyrogram.types import InlineKeyboardMarkup
from asyncio.subprocess import PIPE, create_subprocess_exec as exec
from pyrogram.filters import regex
from pyrogram import filters
from bot import Bot, ALLOWED_CHATS, ALLOWED_USERS, OWNER_ID
from pyrogram.handlers import CallbackQueryHandler, MessageHandler
from json import loads as jsonloads
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.menu_utils import Menus, rcloneListButtonMaker, rcloneListNextPage
from bot.helper.ext_utils.message_utils import editMessage, sendMarkup, sendMessage
from bot.helper.ext_utils.misc_utils import ButtonMaker, get_rclone_config
from bot.helper.ext_utils.var_holder import get_rclone_var, get_val, set_rclone_var, set_val
from bot.modules.myfiles_settings import settings_myfiles_menu

folder_icon= "📁"

async def myfiles_menu(client, message,  msg ="",  edit=False,  drive_name="",  drive_base="",  data_cb="", 
                        submenu="", data_back_cb=""):
    
    if message.reply_to_message:
        user_id= message.reply_to_message.from_user.id
    else:
        user_id= message.from_user.id

    buttons = ButtonMaker()

    if submenu == "list_drive":
        path= ospath.join(getcwd(), "users", str(user_id), "rclone.conf")
        conf = ConfigParser()
        conf.read(path)

        for j in conf.sections():
            if "team_drive" in list(conf[j]):
                buttons.cb_buildsecbutton(f"{folder_icon} {j}", f"myfilesmenu^{data_cb}^{j}^{user_id}")
            else:
                buttons.cb_buildsecbutton(f"{folder_icon} {j}", f"myfilesmenu^{data_cb}^{j}^{user_id}")

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
            await editMessage(msg, message, reply_markup= InlineKeyboardMarkup(buttons.first_button))
        else:
            await sendMarkup(msg, message, reply_markup= InlineKeyboardMarkup(buttons.first_button))

    elif submenu == "list_dir":
        path = get_rclone_config(user_id)
        buttons.cbl_buildbutton(f"⚙️ Folder Settings", f"myfilesmenu^start_folder_actions^{user_id}")
    
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
        set_val("list_info", list_info)

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
                    callback = data_cb,
                    user_id= user_id)

            if offset == 0 and total <= 10:
               buttons.cbl_buildbutton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", data="myfilesmenu^pages") 
            else: 
               buttons.dbuildbutton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", "myfilesmenu^pages",
                                     "NEXT ⏩", f"n_myfiles {next_offset} {data_back_cb}")   

        buttons.cbl_buildbutton("⬅️ Back", f"myfilesmenu^{data_back_cb}^{user_id}")
        buttons.cbl_buildbutton("✘ Close Menu", f"myfilesmenu^close^{user_id}")

        if edit:
            await editMessage(msg, message, reply_markup= InlineKeyboardMarkup(buttons.first_button))
        else:
            await sendMarkup(msg, message, reply_markup= InlineKeyboardMarkup(buttons.first_button))

async def setting_myfiles(client, callback_query):
    query= callback_query
    data = query.data
    cmd = data.split("^")
    message = query.message
    user_id= str(query.from_user.id)
    base_dir= get_rclone_var("MYFILES_BASE_DIR", user_id)
    rclone_drive = get_rclone_var("MYFILES_DRIVE", user_id)

    if query.data == "pages":
        await query.answer()

    if cmd[-1] != user_id:
        await query.answer("This menu is not for you!", show_alert=True)
        return

    if cmd[1] == "list_drive_myfiles_menu":
             
        #Clean Menu
        set_rclone_var("MYFILES_BASE_DIR", "", user_id)
        base_dir= get_rclone_var("MYFILES_BASE_DIR", user_id)
             
        drive_name= cmd[2]     
        set_rclone_var("MYFILES_DRIVE", drive_name, user_id)
        await myfiles_menu(
            client, 
            message, 
            edit=True,
            msg=f"Your drive files are listed below\n\nPath:`{drive_name}:{base_dir}`", 
            drive_name= drive_name, 
            submenu="list_dir", 
            data_cb="list_dir_myfiles_menu", 
            data_back_cb= "myfiles_menu_back")     

    elif cmd[1] == "list_dir_myfiles_menu":
        path = get_val(cmd[2])
        base_dir += path + "/"
        set_rclone_var("MYFILES_BASE_DIR", base_dir, user_id)
        await myfiles_menu(
            client, 
            message, 
            edit=True, 
            msg=f"Your drive files are listed below\n\nPath:`{rclone_drive}:{base_dir}`", 
            drive_base=base_dir, 
            drive_name= rclone_drive, 
            submenu="list_dir", 
            data_cb="list_dir_myfiles_menu", 
            data_back_cb= "myfiles_back")

    elif cmd[1] == "start_file_actions":
        path = get_val(cmd[2])
        base_dir += path
        set_rclone_var("MYFILES_BASE_DIR", base_dir, user_id) 
        await settings_myfiles_menu(
            client, 
            message,
            msg= f"Path:`{rclone_drive}:{base_dir}`",
            drive_base= base_dir,
            edit=True, 
            submenu="myfiles_menu_setting",
            is_folder= False)

    elif cmd[1] == "start_folder_actions":
        await settings_myfiles_menu(
            client, 
            message,
            msg= f"Path:`{rclone_drive}:{base_dir}`", 
            drive_base= base_dir,
            edit=True, 
            submenu="myfiles_menu_setting",
            is_folder= True)

    # Handle back button
    elif cmd[1] == "myfiles_back":
        base_dir_split= base_dir.split("/")[:-2]
        base_dir_string = "" 
        for dir in base_dir_split: 
            base_dir_string += dir + "/"
        base_dir = base_dir_string
        set_rclone_var("MYFILES_BASE_DIR", base_dir, user_id)
        
        if len(base_dir) > 0: 
            data_b_cb= cmd[1]  
        else:
            data_b_cb= "myfiles_menu_back"

        await myfiles_menu(
            client,
            message, 
            msg=f"Path:`{rclone_drive}:{base_dir}`", 
            drive_base= base_dir, 
            drive_name= rclone_drive, 
            submenu="list_dir", 
            data_cb="list_dir_myfiles_menu", 
            edit=True, 
            data_back_cb= data_b_cb)   

    elif cmd[1]== "myfiles_menu_back":
        await myfiles_menu(
            client, 
            message, 
            msg= "Please select your drive to see files",
            submenu= "list_drive",
            data_cb= "list_drive_myfiles_menu",
            edit=True)     

    #Handling actions

    if cmd[1] == "delete_action":
        if cmd[2] == "folder":
            is_folder= True
        elif cmd[2] == "file":
            is_folder= False

        await settings_myfiles_menu(
            client, 
            message,
            drive_base= base_dir, 
            drive_name= rclone_drive, 
            edit=True, 
            submenu= "rclone_delete",
            is_folder= is_folder)

    elif cmd[1] == "size_action":
        await settings_myfiles_menu(
            client, 
            message,
            drive_base= base_dir, 
            drive_name= rclone_drive, 
            submenu= "rclone_size", 
            edit=True)

    if cmd[1] == "close":
        await query.answer("Closed")
        await message.delete()

    #Handling purge delete dialog

    if cmd[1]== "yes":
        if cmd[2] == "folder":
            is_folder= True
        elif cmd[2] == "file":
            is_folder= False

        await settings_myfiles_menu(
            client, 
            message,
            drive_base= base_dir, 
            drive_name= rclone_drive, 
            edit=True, 
            submenu= "yes",
            is_folder= is_folder)

    elif cmd[1]== "no":
        await query.answer("Closed") 
        await message.delete()

async def next_page_myfiles(client, callback_query):
    data= callback_query.data
    message= callback_query.message
    user_id= message.reply_to_message.from_user.id
    _, next_offset, data_back_cb = data.split()
    list_info = get_val("list_info")
    total = len(list_info)
    next_offset = int(next_offset)
    prev_offset = next_offset - 10 

    buttons = ButtonMaker()
    buttons.cbl_buildbutton(f"⚙️ Folder Settings", f"myfilesmenu^start_folder_actions^{user_id}")

    next_list_info, _next_offset= rcloneListNextPage(list_info, next_offset)

    rcloneListButtonMaker(result_list= next_list_info,
        buttons=buttons,
        menu_type= Menus.MYFILES, 
        callback = "list_dir_myfiles_menu",
        user_id= user_id)

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

    buttons.cbl_buildbutton("⬅️ Back", f"myfilesmenu^{data_back_cb}^{user_id}")
    buttons.cbl_buildbutton("✘ Close Menu", f"myfilesmenu^close^{user_id}")

    default_drive= get_rclone_var("MYFILES_DRIVE", user_id)
    base_dir= get_rclone_var("MYFILES_BASE_DIR", user_id)
    await editMessage(f"Your drive files are listed below\n\nPath:`{default_drive}:{base_dir}`", message, 
                      reply_markup= InlineKeyboardMarkup(buttons.first_button))

async def handle_myfiles(client, message):
    user_id= message.from_user.id
    chat_id = message.chat.id
    if user_id in ALLOWED_USERS or chat_id in ALLOWED_CHATS or user_id == OWNER_ID:
         await myfiles_menu(
                client, 
                message,
                msg= "Please select your drive to see files", 
                submenu="list_drive",
                data_cb="list_drive_myfiles_menu")
    else:
        await message.reply('Not Authorized user', quote=True)

next_page_myfiles_cb= CallbackQueryHandler(
                next_page_myfiles,
                filters= regex("n_myfiles"))
Bot.add_handler(next_page_myfiles_cb)

setting_myfiles_cb = CallbackQueryHandler(
                setting_myfiles,
                filters= regex("myfilesmenu"))
Bot.add_handler(setting_myfiles_cb)

myfiles_handler = MessageHandler(
        handle_myfiles,
        filters= filters.command(BotCommands.MyFilesCommand))
Bot.add_handler(myfiles_handler)