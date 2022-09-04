from json import loads as jsonloads
from os import path as ospath, getcwd
from bot.utils.bot_commands import BotCommands
from configparser import ConfigParser
from asyncio.subprocess import PIPE, create_subprocess_exec as exec
from pyrogram.types import InlineKeyboardMarkup
from pyrogram.filters import regex, command
from bot import ALLOWED_CHATS, ALLOWED_USERS, DOWNLOAD_DIR, OWNER_ID, Bot
from pyrogram.handlers import CallbackQueryHandler, MessageHandler
from bot.utils.var_holder import get_rclone_var, get_val, set_rclone_var, set_val
from bot.uploaders.rclone.rclone_leech import RcloneLeech
from bot.utils.bot_utils.menu_utils import Menus, rcloneListButtonMaker, rcloneListNextPage
from bot.utils.bot_utils.message_utils import editMessage, sendMarkup, sendMessage
from bot.utils.bot_utils.misc_utils import ButtonMaker, get_rclone_config, pairwise

folder_icon= "📁"

async def handle_zip_leech_command(client, message):
    await leech(client, message, isZip=True)

async def handle_unzip_leech_command(client, message):
    await leech(client, message, extract=True)

async def handle_leech(client, message):
    await leech(client, message)

async def leech(client, message, isZip=False, extract=False):
    user_id= message.from_user.id
    chat_id = message.chat.id
    if user_id in ALLOWED_USERS or chat_id in ALLOWED_CHATS or user_id == OWNER_ID:
        set_val('IS_ZIP', isZip)   
        set_val('EXTRACT', extract)    
        await leech_menu(client, message,msg= "Select cloud where your files are stored",
                submenu= "list_drive",data_cb="list_drive_leech_menu") 
    else:
        await message.reply('Not Authorized user', quote= True)

async def leech_menu(client, message, msg="",edit=False, drive_base="", drive_name="", submenu="", 
                    data_cb="", data_back_cb=""):

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
                buttons.cb_buildsecbutton(f"{folder_icon} {j}", f"leechmenu^{data_cb}^{j}^{user_id}")     
            else:
                buttons.cb_buildsecbutton(f"{folder_icon} {j}", f"leechmenu^{data_cb}^{j}^{user_id}")          
        
        for a, b in pairwise(buttons.second_button):
            row= []
            if b == None:
                row.append(a)     
                buttons.ap_buildbutton(row)
                break
            row.append(a)
            row.append(b)
            buttons.ap_buildbutton(row)
            
        buttons.cbl_buildbutton("✘ Close Menu", f"leechmenu^close^{user_id}")

        if edit:
            await editMessage(msg, message, reply_markup= InlineKeyboardMarkup(buttons.first_button))
        else:
            await sendMarkup(msg, message, reply_markup= InlineKeyboardMarkup(buttons.first_button))

    elif submenu == "list_dir":
        path = get_rclone_config(user_id)
        buttons.cbl_buildbutton("✅ Select this folder", data=f"leechmenu^start_leech_folder^{user_id}")
        
        cmd = ["rclone", "lsjson", f'--config={path}', f"{drive_name}:{drive_base}"]
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
            buttons.cbl_buildbutton("❌Nothing to show❌", data=f"leechmenu^pages^{user_id}")   
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
                menu_type= Menus.LEECH, 
                callback = data_cb,
                user_id= user_id)

            if offset == 0 and total <= 10:
                buttons.cbl_buildbutton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", data=f"leechmenu^pages^{user_id}")        
            else: 
                buttons.dbuildbutton(first_text= f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", first_callback=f"leechmenu^pages^{user_id}",
                                second_text= "NEXT ⏩", second_callback= f"next_leech {next_offset} {data_back_cb}")
    
        buttons.cbl_buildbutton("⬅️ Back", data= f"leechmenu^{data_back_cb}^{user_id}")
        buttons.cbl_buildbutton("✘ Close Menu", data=f"leechmenu^close^{user_id}")

        if edit:
            await editMessage(msg, message, reply_markup= InlineKeyboardMarkup(buttons.first_button))
        else:
            await sendMarkup(msg, message, reply_markup= InlineKeyboardMarkup(buttons.first_button))

async def leech_menu_cb(client, callback_query):
    query= callback_query
    data = query.data
    cmd = data.split("^")
    message = query.message
    user_id= str(query.from_user.id)
    tag = f"@{message.reply_to_message.from_user.username}"
    base_dir= get_rclone_var("LEECH_BASE_DIR", user_id)
    rclone_drive = get_rclone_var("LEECH_DRIVE", user_id)
    is_zip = False
    extract = False

    msg= 'Select folder or file that you want to leech\n'
    if get_val('IS_ZIP'):
        msg= 'Select file that you want to zip\n' 
        is_zip= True
        
    if get_val('EXTRACT'):
        msg= 'Select file that you want to extract\n'
        extract= True

    if data == "pages":
        await query.answer()

    if cmd[-1] != user_id:
        await query.answer("This menu is not for you!", show_alert=True)
        return

    if cmd[1] == "list_drive_leech_menu":
        drive_name= cmd[2]

        #reset menu
        set_rclone_var("LEECH_BASE_DIR", "", user_id)
        base_dir= get_rclone_var("LEECH_BASE_DIR", user_id)

        set_rclone_var("LEECH_DRIVE", drive_name, user_id)
        await leech_menu(
            client, 
            message, 
            msg=f"{msg}\nPath:`{drive_name}:{base_dir}`", 
            drive_name= drive_name, 
            submenu="list_dir", 
            data_cb="list_dir_leech_menu",
            edit=True, 
            data_back_cb= "leech_menu_back")     

    elif cmd[1] == "list_dir_leech_menu":
        path = get_val(cmd[2])
        base_dir += path + "/"
        set_rclone_var("LEECH_BASE_DIR", base_dir, user_id)
        await leech_menu(
            client, 
            message, 
            edit=True, 
            msg=f"{msg}\nPath:`{rclone_drive}:{base_dir}`", 
            drive_base= base_dir, 
            drive_name= rclone_drive, 
            submenu="list_dir", 
            data_cb="list_dir_leech_menu", 
            data_back_cb= "leech_back")

    elif cmd[1] == "start_leech_file":
        path = get_val(cmd[2])
        base_dir += path
        dest_dir = f'{DOWNLOAD_DIR}{path}'
        rclone_leech= RcloneLeech(message, user_id, base_dir, dest_dir, path, tag= tag, isZip=is_zip, extract=extract)
        await rclone_leech.leech()

    elif cmd[1] == "start_leech_folder":
        dest_dir = f'{DOWNLOAD_DIR}{base_dir}'
        rclone_leech= RcloneLeech(message, user_id, base_dir, dest_dir, tag= tag, isZip=is_zip, extract=extract, folder=True)
        await rclone_leech.leech()

    elif cmd[1] == "leech_back":
        base_dir_split= base_dir.split("/")[:-2]
        base_dir_string = "" 
        for dir in base_dir_split: 
            base_dir_string += dir + "/"
        base_dir = base_dir_string
        set_rclone_var("LEECH_BASE_DIR", base_dir, user_id)
        
        if len(base_dir) > 0: 
            data_b_cb= cmd[1]  
        else:
            data_b_cb= "leech_menu_back"

        await leech_menu(
            client,
            message, 
            edit=True, 
            msg=f"{msg}\nPath:`{rclone_drive}:{base_dir}`", 
            drive_base= base_dir, 
            drive_name= rclone_drive, 
            submenu="list_dir", 
            data_cb="list_dir_leech_menu", 
            data_back_cb= data_b_cb)   

    elif cmd[1]== "leech_menu_back":
        await leech_menu(
            client, 
            message, 
            msg= "Select cloud where your files are stored",
            submenu= "list_drive",
            data_cb="list_drive_leech_menu",
            edit=True)     

    elif cmd[1] == "close":
        await query.answer("Closed")
        set_rclone_var("LEECH_BASE_DIR", "", user_id)
        await message.delete()
 
async def next_page_leech(client, callback_query):
    data = callback_query.data
    message= callback_query.message
    user_id= message.reply_to_message.from_user.id
    _, next_offset, data_back_cb= data.split()
    list_info = get_val("list_info")
    total = len(list_info)
    next_offset = int(next_offset)
    prev_offset = next_offset - 10 

    buttons = ButtonMaker()
    buttons.cbl_buildbutton(f"✅ Select this folder", data= f"leechmenu^start_leech_folder^{user_id}")

    next_list_info, _next_offset= rcloneListNextPage(list_info, next_offset)

    rcloneListButtonMaker(result_list= next_list_info,
        buttons=buttons,
        menu_type= Menus.LEECH, 
        callback = "list_dir_leech_menu",
        user_id= user_id)

    if next_offset == 0:
        buttons.dbuildbutton(first_text = f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", first_callback="setting pages", 
                            second_text= "NEXT ⏩", second_callback= f"next_leech {_next_offset} {data_back_cb}" )
    
    elif next_offset >= total:
        buttons.dbuildbutton(first_text="⏪ BACK", first_callback= f"next_leech {prev_offset} {data_back_cb}", 
                        second_text=f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", second_callback="setting pages")
   
    elif next_offset + 10 > total:
        buttons.dbuildbutton(first_text="⏪ BACK", first_callback= f"next_leech {prev_offset} {data_back_cb}", 
                        second_text= f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", second_callback="setting pages")                               
    else:
        buttons.tbuildbutton(first_text="⏪ BACK", first_callback= f"next_leech {prev_offset} {data_back_cb}", 
                            second_text= f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", second_callback="setting pages",
                            third_text="NEXT ⏩", third_callback=f"next_leech {_next_offset} {data_back_cb}")

    buttons.cbl_buildbutton("⬅️ Back", f"leechmenu^{data_back_cb}^{user_id}")
    buttons.cbl_buildbutton("✘ Close Menu", f"leechmenu^close^{user_id}")

    default_drive= get_rclone_var("LEECH_DRIVE", user_id)
    base_dir= get_rclone_var("LEECH_BASE_DIR", user_id)
    await editMessage(f"Select folder or file that you want to leech\n\nPath:`{default_drive}:{base_dir}`", message, 
                        reply_markup= InlineKeyboardMarkup(buttons.first_button))    
           

next_page_cbq= CallbackQueryHandler(next_page_leech,filters= regex("next_leech"))
leech_menu_cbq= CallbackQueryHandler(leech_menu_cb,filters= regex("leechmenu"))
leech_handler = MessageHandler(handle_leech,filters= command(BotCommands.LeechCommand))
zip_leech_handler = MessageHandler(handle_zip_leech_command,filters= command(BotCommands.ZipLeechCommand))
unzip_leech_handler = MessageHandler(handle_unzip_leech_command,filters= command(BotCommands.UnzipLeechCommand))

Bot.add_handler(next_page_cbq)
Bot.add_handler(leech_menu_cbq)
Bot.add_handler(leech_handler)
Bot.add_handler(zip_leech_handler)
Bot.add_handler(unzip_leech_handler)