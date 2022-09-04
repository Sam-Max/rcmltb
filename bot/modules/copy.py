import configparser
from asyncio.subprocess import PIPE, create_subprocess_exec as exec
from json import loads as jsonloads
from bot import ALLOWED_CHATS, ALLOWED_USERS, bot
from bot import bot, ALLOWED_CHATS, ALLOWED_USERS, OWNER_ID
from bot.utils.bot_commands import BotCommands
from telethon.events import NewMessage
from bot.utils.var_holder import get_rclone_var, get_val, set_rclone_var, set_val
from os import path as ospath, getcwd
from bot.uploaders.rclone.rclone_copy import RcloneCopy
from bot.utils.bot_utils.bot_utils import command_process
from telethon.events import CallbackQuery
from bot.utils.bot_utils.menu_utils import Menus, rcloneListButtonMaker, rcloneListNextPage
from bot.utils.bot_utils.misc_utils import TelethonButtonMaker, get_rclone_config, pairwise

folder_icon= "📁"

async def copy_menu(query, msg="", submenu="", drive_base="", drive_name="", data_cb="", data_back_cb="",
                     edit=False, is_second_menu= False):
    
    user_id= query.sender_id
    buttons = TelethonButtonMaker()

    if submenu == "list_drive":
        path= ospath.join(getcwd(), "users", str(user_id), "rclone.conf")
        conf = configparser.ConfigParser()
        conf.read(path)

        for j in conf.sections():
            if "team_drive" in list(conf[j]):
                buttons.cb_buildsecbutton(f"{folder_icon} {j}", f"copymenu^{data_cb}^{j}^{user_id}")
            else:
                buttons.cb_buildsecbutton(f"{folder_icon} {j}", f"copymenu^{data_cb}^{j}^{user_id}")
        
        for a, b in pairwise(buttons.second_button):
            row= [] 
            if b == None:
                row.append(a)  
                buttons.ap_buildbutton(row)
                break
            row.append(a)
            row.append(b)
            buttons.ap_buildbutton(row)

        buttons.cbl_buildbutton("✘ Close Menu", f"copymenu^close^{user_id}")

        if edit:
            await query.edit(msg, buttons= buttons.first_button)
        else:
            await query.reply(msg, buttons= buttons.first_button)

    elif submenu == "list_dir":
        conf_path = get_rclone_config(user_id)

        if is_second_menu:
            buttons.cbl_buildbutton(f"✅ Select this folder", f"copymenu^start_copy^{user_id}")
            cmd = ["rclone", "lsjson", f'--config={conf_path}', f"{drive_name}:{drive_base}", "--dirs-only"] 
        else:
            buttons.cbl_buildbutton(f"✅ Select this folder", f"copymenu^list_drive_second_menu^_^False^{user_id}")
            cmd = ["rclone", "lsjson", f'--config={conf_path}', f"{drive_name}:{drive_base}"] 

        process = await exec(*cmd, stdout=PIPE, stderr=PIPE)
        out, err = await process.communicate()
        out = out.decode().strip()
        return_code = await process.wait()

        if return_code != 0:
           err = err.decode().strip()
           return await query.reply(f'Error: {err}')  

        list_info = jsonloads(out)
        if is_second_menu:
            list_info.sort(key=lambda x: x["Name"]) 
        else:
            list_info.sort(key=lambda x: x["Size"])  
        set_val("list_info", list_info) 

        if len(list_info) == 0:
            buttons.cbl_buildbutton("❌Nothing to show❌", data="copymenu^pages^{user_id}")
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
        
            rcloneListButtonMaker(result_list=list_info, 
                buttons= buttons, 
                menu_type = Menus.COPY,
                callback= data_cb,
                is_second_menu = is_second_menu,
                user_id= user_id)

            if offset == 0 and total <= 10:
                buttons.cbl_buildbutton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", "copymenu^pages^{user_id}") 
            else: 
                buttons.dbuildbutton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", "copymenu^pages^{user_id}",
                                    "NEXT ⏩", f"next_copy {next_offset} {is_second_menu} {data_back_cb}")

        buttons.cbl_buildbutton("⬅️ Back", f"copymenu^{data_back_cb}^{user_id}")
        buttons.cbl_buildbutton("✘ Close Menu", f"copymenu^close^{user_id}")

        if edit:
            await query.edit(msg, buttons=buttons.first_button)
        else:
            await query.reply(msg, buttons=buttons.first_button)

async def setting_copy_menu(callback_query):
    query= callback_query
    data = query.data.decode()
    cmd = data.split("^")
    message = await query.get_message()
    user_id= str(callback_query.sender_id)
    origin_drive = get_rclone_var("COPY_ORIGIN_DRIVE", user_id)
    origin_dir= get_rclone_var("COPY_ORIGIN_DIR", user_id)
    dest_drive= get_rclone_var("COPY_DESTINATION_DRIVE", user_id)
    dest_dir= get_rclone_var("COPY_DESTINATION_DIR", user_id)

    if query.data == "pages":
        await query.answer()

    if cmd[-1] != user_id:
        await query.answer("This menu is not for you!", alert=True)
        return

    #First Menu
    if cmd[1] == "list_drive_origin":
        origin_drive= cmd[2]

        #Clean Menu
        set_rclone_var("COPY_ORIGIN_DIR", "", user_id)
        origin_dir= get_rclone_var("COPY_ORIGIN_DIR", user_id)
        
        set_rclone_var("COPY_ORIGIN_DRIVE", origin_drive, user_id)
        await copy_menu(
            query= query, 
            msg= f'Select file or folder which you want to copy\n\nPath: `{origin_drive}:{origin_dir}`', 
            drive_name= origin_drive,
            submenu="list_dir", 
            data_cb="list_dir_origin",
            edit=True,
            data_back_cb= "origin_menu_back")

    elif cmd[1] == "list_dir_origin":
        path = get_val(cmd[2])
        origin_dir_= origin_dir + path  + "/"
        set_rclone_var("COPY_ORIGIN_DIR", origin_dir_, user_id)
        await copy_menu(
             query,
             msg=f"Select file or folder which you want to copy\n\nPath:`{origin_drive}:{origin_dir_}`", 
             drive_base= origin_dir_, 
             drive_name= origin_drive,
             submenu="list_dir",
             data_cb="list_dir_origin",
             edit=True,
             data_back_cb="first_menu_back")

    #Second Menu
    elif cmd[1] == "list_drive_second_menu":
        if cmd[3] == "True":
            path = get_val(cmd[2])
            origin_dir_= origin_dir + path  
            set_rclone_var("COPY_ORIGIN_DIR", origin_dir_, user_id)    
        await copy_menu(
            query, 
            msg=f'Select folder where you want to copy\n', 
            submenu="list_drive", 
            data_cb="list_drive_dest",
            edit=True, 
            is_second_menu=True)

    elif cmd[1] == "list_drive_dest":
        dest_drive= cmd[2]

        #Clean Menu
        set_rclone_var("COPY_DESTINATION_DIR", "", user_id)
        dest_dir= get_rclone_var("COPY_DESTINATION_DIR", user_id)     

        set_rclone_var("COPY_DESTINATION_DRIVE", dest_drive, user_id)
        await copy_menu(
            query, 
            edit=True, 
            msg=f'Select folder where you want to copy\n\nPath:`{dest_drive}:{dest_dir}`',
            drive_name= dest_drive,
            submenu="list_dir", 
            data_cb="list_dir_dest",
            data_back_cb= "dest_menu_back",
            is_second_menu=True)

    elif cmd[1] == "list_dir_dest":
        path = get_val(cmd[2])
        dest_dir_= f"{dest_dir}{path}/"
        set_rclone_var("COPY_DESTINATION_DIR", dest_dir_, user_id)
        await copy_menu(
             query,
             edit=True, 
             msg=f"Select folder where you want to copy\n\nPath:`{dest_drive}:{dest_dir_}`", 
             drive_name= dest_drive,
             drive_base= dest_dir_, 
             submenu="list_dir",
             data_cb="list_dir_dest",
             data_back_cb= "second_menu_back",
             is_second_menu= True)        
 
    elif cmd[1] == "start_copy":
        set_val("COPY_DESTINATION_DIR", dest_dir)
        rclone_copy= RcloneCopy(message, user_id)
        await rclone_copy.copy()

    elif cmd[1] == "close":
        await query.answer("Closed")
        await query.delete()

    # Origin Menu Back Button
    elif cmd[1] == "first_menu_back":
        origin_dir_list= origin_dir.split("/")[:-2]
        origin_dir_string = "" 
        for dir in origin_dir_list: 
            origin_dir_string += dir + "/" 
        origin_dir= origin_dir_string
        set_rclone_var("COPY_ORIGIN_DIR", origin_dir, user_id)

        if len(origin_dir) > 0: 
            data_b_cb= cmd[1]  
        else:
            data_b_cb= "origin_menu_back"

        await copy_menu(
             query,
             msg=f"Select file or folder which you want to copy\n\nPath:`{origin_drive}:{origin_dir}`", 
             drive_base=origin_dir, 
             drive_name= origin_drive,
             submenu="list_dir",
             data_cb="list_dir_origin",
             data_back_cb= data_b_cb,
             edit=True, 
             is_second_menu= False)   
    
    elif cmd[1]== "origin_menu_back":
        await copy_menu(
            query, 
            msg= "Select cloud where your files are stored",
            submenu= "list_drive",
            data_cb="list_drive_origin",
            edit=True)

    # Destination Menu Back Button

    elif cmd[1] == "second_menu_back":
        dest_dir_list= dest_dir.split("/")[:-2]
        dest_dir_string = "" 
        for dir in dest_dir_list: 
            dest_dir_string += dir + "/"
        dest_dir= dest_dir_string
        set_rclone_var("COPY_DESTINATION_DIR", dest_dir, user_id)
        
        if len(dest_dir) > 0: 
            data_b_cb= cmd[1]  
        else:
            data_b_cb= "dest_menu_back"

        await copy_menu(
             query,
             msg=f"Select folder where you want to copy\n\nPath:`{dest_drive}:{dest_dir}`", 
             drive_base= dest_dir, 
             drive_name= dest_drive,
             submenu="list_dir", 
             data_cb="list_dir_dest",
             data_back_cb= data_b_cb,
             edit=True, 
             is_second_menu= True)   

    elif cmd[1]== "dest_menu_back":
        await copy_menu(
            query, 
            msg= f"Select cloud where to copy files", 
            submenu= "list_drive",
            data_cb="list_drive_dest",
            edit=True)          

async def next_page_copy(callback_query):
    data= callback_query.data
    message= await callback_query.get_message()
    user_id= callback_query.sender_id
    _, next_offset, is_second_menu, data_back_cb = data.decode().split()
    is_second_menu = is_second_menu.lower() == 'true'
    list_info = get_val("list_info")
    total = len(list_info)
    next_offset = int(next_offset)
    prev_offset = next_offset - 10 
    
    buttons = TelethonButtonMaker()
    next_list_info, _next_offset= rcloneListNextPage(list_info, next_offset) 

    if is_second_menu:
        buttons.cbl_buildbutton("✅ Select this folder", f"copymenu^start_copy^{user_id}")
    else:
        buttons.cbl_buildbutton("✅ Select this folder", f"copymenu^rclone_menu_copy^_^False^{user_id}")
    
    if is_second_menu:
        rcloneListButtonMaker(result_list= next_list_info, 
            buttons= buttons,
            menu_type= Menus.COPY,
            callback= "list_dir_dest",
            user_id= user_id,
            is_second_menu= is_second_menu)
    else:
        rcloneListButtonMaker(result_list= next_list_info, 
            buttons= buttons,
            menu_type= Menus.COPY,
            callback= "list_dir_origin",
            user_id= user_id,
            is_second_menu=is_second_menu)

    if next_offset == 0:
        buttons.dbuildbutton(f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", "setting pages",
                            "NEXT ⏩", f"next_copy {_next_offset} {is_second_menu} {data_back_cb}")
    
    elif next_offset >= total:
        buttons.dbuildbutton("⏪ BACK", f"next_copy {prev_offset} {is_second_menu} {data_back_cb}",
                            f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}",
                                   "setting pages")

    elif next_offset + 10 > total:
        buttons.dbuildbutton("⏪ BACK", f"next_copy {prev_offset} {is_second_menu} {data_back_cb}",
                            f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}","setting pages")                               
    else:
        buttons.tbuildbutton("⏪ BACK", f"next_copy {prev_offset} {is_second_menu} {data_back_cb}",
                            f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", "setting pages",
                            "NEXT ⏩", f"next_copy {_next_offset} {is_second_menu} {data_back_cb}")

    buttons.cbl_buildbutton("⬅️ Back", f"copymenu^{data_back_cb}^{user_id}")
    buttons.cbl_buildbutton("✘ Close Menu", f"copymenu^close^{user_id}")
                            
    if is_second_menu:
        dest_drive= get_rclone_var("COPY_DESTINATION_DRIVE", user_id)
        dest_dir= get_rclone_var("COPY_DESTINATION_DIR", user_id)
        await message.edit(f"Select folder where you want to copy\n\nPath:`{dest_drive}:{dest_dir}`", buttons=buttons.first_button)
    else:
        origin_drive= get_rclone_var("COPY_ORIGIN_DRIVE", user_id)
        origin_dir= get_rclone_var("COPY_ORIGIN_DIR", user_id)
        await message.edit(f"Select file or folder which you want to copy\n\nPath:`{origin_drive}:{origin_dir}`", buttons=buttons.first_button)

async def handle_copy(event):
    user_id= event.sender_id
    if user_id in ALLOWED_USERS or event.chat_id in ALLOWED_CHATS or user_id == OWNER_ID:
        path= ospath.join(getcwd(), "users", str(user_id), "rclone.conf")
        if not ospath.exists(path):
            msg= f"Load an rclone config file, use /config"
            await event.reply(msg)
        else:
            origin_dir= get_rclone_var("COPY_ORIGIN_DIR", user_id)
            origin_drive = get_rclone_var("COPY_ORIGIN_DRIVE", user_id)     
            await copy_menu(event, msg= f"Select cloud where your files are stored\n\nPath:`{origin_drive}:{origin_dir}`", 
                    submenu= "list_drive", data_cb= "list_drive_origin")
    else:
        await event.reply('Not Authorized user')      

bot.add_event_handler(handle_copy, NewMessage(pattern= command_process(f"/{BotCommands.CopyCommand}")))
bot.add_event_handler(next_page_copy, CallbackQuery(pattern="next_copy"))
bot.add_event_handler(setting_copy_menu, CallbackQuery(pattern="copymenu"))