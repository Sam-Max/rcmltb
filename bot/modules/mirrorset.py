from asyncio.subprocess import PIPE, create_subprocess_exec as exec
from os import path as ospath, getcwd
import configparser
from bot import ALLOWED_CHATS, ALLOWED_USERS, OWNER_ID, bot
from telethon.events import CallbackQuery, NewMessage
from json import loads as jsonloads
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.bot_utils import command_process
from bot.helper.ext_utils.menu_utils import Menus, rcloneListButtonMaker, rcloneListNextPage
from bot.helper.ext_utils.misc_utils import TelethonButtonMaker, get_rclone_config, pairwise
from bot.helper.ext_utils.var_holder import get_rclone_var, get_val, set_rclone_var, set_val

yes = "✅"
folder_icon= "📁"

async def mirrorset_menu(query, msg="", submenu="", drive_base="", drive_name="", edit=False, 
                         data_cb="", data_back_cb= ""):
    
    user_id= query.sender_id
    buttons = TelethonButtonMaker()

    if submenu == "list_drive":
        path= ospath.join(getcwd(), "users", str(user_id), "rclone.conf")
        conf = configparser.ConfigParser()
        conf.read(path)

        for drive in conf.sections():
            prev = ""
            if drive == get_rclone_var(f"MIRRORSET_DRIVE", user_id):
                prev = yes
            if "team_drive" in list(conf[drive]):
                buttons.cb_buildsecbutton(f"{prev} {folder_icon} {drive}", f"mirrorsetmenu^list_drive_ms_menu^{drive}^{user_id}")
            else:
                buttons.cb_buildsecbutton(f"{prev} {folder_icon} {drive}", f"mirrorsetmenu^list_drive_ms_menu^{drive}^{user_id}")
        
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

        if edit:
            await query.edit(msg, buttons=buttons.first_button)
        else:
            await query.reply(msg, buttons=buttons.first_button)

    elif submenu == "list_dir":
        conf_path = get_rclone_config(user_id)
        buttons.cbl_buildbutton(f"✅ Select this folder", f"mirrorsetmenu^close^{user_id}")
        cmd = ["rclone", "lsjson", f'--config={conf_path}', f"{drive_name}:{drive_base}", "--dirs-only"] 

        process = await exec(*cmd, stdout=PIPE, stderr=PIPE)
        out, err = await process.communicate()
        out = out.decode().strip()
        return_code = await process.wait()
        
        if return_code != 0:
           err = err.decode().strip()
           return await query.reply(f'Error: {err}')  

        list_info = jsonloads(out)
        list_info.sort(key=lambda x: x["Name"])  
        set_val("list_info", list_info)

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
  
            rcloneListButtonMaker(result_list=list_info, 
                buttons= buttons, 
                menu_type= Menus.MIRRORSET,
                callback= data_cb,
                user_id= user_id)

            if offset == 0 and total <= 10:
                buttons.cbl_buildbutton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", f"mirrorsetmenu^pages^{user_id}") 
            else: 
                buttons.dbuildbutton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", f"mirrorsetmenu^pages^{user_id}",
                                    "NEXT ⏩", f"n_mirrorset {next_offset} {data_back_cb}")

        buttons.cbl_buildbutton("⬅️ Back", f"mirrorsetmenu^{data_back_cb}^{user_id}")
        buttons.cbl_buildbutton("✘ Close Menu", f"mirrorsetmenu^close^{user_id}")

        if edit:
            await query.edit(msg, buttons=buttons.first_button)
        else:
            await query.reply(msg, buttons=buttons.first_button)

async def setting_mirroset(callback_query):
    query= callback_query
    data = query.data.decode()
    cmd = data.split("^")
    user_id= str(query.sender_id)
    base_dir= get_rclone_var("MIRRORSET_BASE_DIR", user_id)
    rclone_drive = get_rclone_var("MIRRORSET_DRIVE", user_id)

    if query.data == "pages":
        await query.answer()

    if cmd[-1] != user_id:
        await query.answer("This menu is not for you!", alert=True)
        return

    elif cmd[1] == "list_drive_ms_menu":
        drive_name= cmd[2]
        
        #reset menu
        set_rclone_var("MIRRORSET_BASE_DIR", "", user_id)
        base_dir= get_rclone_var("MIRRORSET_BASE_DIR", user_id)

        set_rclone_var("MIRRORSET_DRIVE", drive_name, user_id)
        await mirrorset_menu(
            query, 
            msg=f"Select folder where you want to store files\n\nPath:`{drive_name}:{base_dir}`", 
            drive_name= drive_name, 
            submenu="list_dir", 
            edit=True,
            data_cb="list_dir_mirrorset_menu", 
            data_back_cb= "mirrorset_menu_back")     

    elif cmd[1] == "list_dir_mirrorset_menu":
        path = get_val(cmd[2])
        base_dir += path + "/"
        set_rclone_var("MIRRORSET_BASE_DIR", base_dir, user_id)
        await mirrorset_menu(
            query, 
            msg=f"Select folder where you want to store files\n\nPath:`{rclone_drive}:{base_dir}`", 
            drive_base=base_dir, 
            drive_name= rclone_drive, 
            submenu="list_dir", 
            edit=True, 
            data_cb="list_dir_mirrorset_menu", 
            data_back_cb= "mirrorset_back")

    elif cmd[1] == "mirrorset_back":
        base_dir_split= base_dir.split("/")[:-2]
        base_dir_string = "" 
        for dir in base_dir_split: 
            base_dir_string += dir + "/"
        base_dir = base_dir_string
        set_rclone_var("MIRRORSET_BASE_DIR", base_dir, user_id)
        
        if len(base_dir) > 0: 
            data_b_cb= cmd[1]  
        else:
            data_b_cb= "mirrorset_menu_back"

        await mirrorset_menu(
            query,
            msg=f"Select folder where you want to store files\n\nPath:`{rclone_drive}:{base_dir}`", 
            drive_base=base_dir, 
            drive_name= rclone_drive, 
            submenu="list_dir", 
            data_cb="list_dir_mirrorset_menu", 
            edit=True,
            data_back_cb= data_b_cb) 

    elif cmd[1]== "mirrorset_menu_back":
         await mirrorset_menu(
            query, 
            msg= f"Select cloud where you want to upload file\n\nPath:`{rclone_drive}:{base_dir}`",
            submenu="list_drive",
            edit=True)                

    elif cmd[1] == "close":
        await callback_query.answer("Closed")
        await callback_query.delete()

async def next_page_mirrorset(callback_query):
    data= callback_query.data
    message= await callback_query.get_message()
    user_id= callback_query.sender_id
    _, next_offset, data_back_cb = data.decode().split()
    list_info = get_val("list_info")
    total = len(list_info)
    next_offset = int(next_offset)
    prev_offset = next_offset - 10 

    buttons = TelethonButtonMaker()
    buttons.cbl_buildbutton("✅ Select this folder", f"mirrorsetmenu^close^{user_id}")

    next_list_info, _next_offset= rcloneListNextPage(list_info, next_offset) 
    rcloneListButtonMaker(result_list= next_list_info, 
            buttons= buttons,
            menu_type= Menus.MIRRORSET,
            callback="list_dir_mirrorset_menu",
            user_id= user_id)

    if next_offset == 0:
        buttons.dbuildbutton(f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", "setting pages",
                            "NEXT ⏩", f"next_mirrorset {_next_offset} {data_back_cb}")

    elif next_offset >= total:
        buttons.dbuildbutton("⏪ BACK", f"next_mirrorset {prev_offset} {data_back_cb}",
                            f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", "setting pages")

    elif next_offset + 10 > total:
        buttons.dbuildbutton("⏪ BACK", f"next_mirrorset {prev_offset} {data_back_cb}",
                             f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", "setting pages")                              

    else:
        buttons.tbuildbutton("⏪ BACK", f"next_mirrorset {prev_offset} {data_back_cb}",
                            f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", "setting pages",
                            "NEXT ⏩", f"next_mirrorset {_next_offset} {data_back_cb}")

    buttons.cbl_buildbutton("⬅️ Back", f"mirrorsetmenu^{data_back_cb}^{user_id}")
    buttons.cbl_buildbutton("✘ Close Menu", f"mirrorsetmenu^close^{user_id}")

    d_rclone_drive= get_rclone_var("MIRRORSET_DRIVE", user_id)
    base_dir= get_rclone_var("MIRRORSET_BASE_DIR", user_id)
    await message.edit(f"Select folder where you want to store files\n\nPath:`{d_rclone_drive}:{base_dir}`", buttons=buttons.first_button)

async def handle_mirrorset(event):
    user_id= event.sender_id
    if user_id in ALLOWED_USERS or event.chat_id in ALLOWED_CHATS or user_id == OWNER_ID:
            path= ospath.join(getcwd(), "users", str(user_id), "rclone.conf")
            if not ospath.exists(path):
                msg= f"Load an rclone config file, use /config"
                await event.reply(msg)
            else:
                base_dir= get_rclone_var("MIRRORSET_BASE_DIR", user_id)
                rclone_drive = get_rclone_var("MIRRORSET_DRIVE", user_id)          
                msg= f"Select cloud where you want to upload file\n\nPath:`{rclone_drive}:{base_dir}`"      
                await mirrorset_menu(
                    query= event,
                    submenu= "list_drive",
                    msg= msg)
    else:
        await event.reply('Not Authorized user')         

bot.add_event_handler(handle_mirrorset, NewMessage(pattern=command_process(f"/{BotCommands.MirroSetCommand}")))
bot.add_event_handler(next_page_mirrorset, CallbackQuery(pattern="next_mirrorset"))
bot.add_event_handler(setting_mirroset, CallbackQuery(pattern="mirrorsetmenu"))