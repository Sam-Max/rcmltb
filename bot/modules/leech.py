import asyncio
from json import loads as jsonloads
from os import path as ospath, getcwd
from configparser import ConfigParser
from asyncio.subprocess import PIPE, create_subprocess_exec as exec
from pyrogram.types import InlineKeyboardMarkup
from pyrogram.filters import regex, command
from pyrogram.handlers import CallbackQueryHandler, MessageHandler
from pyrogram import filters
from bot import DOWNLOAD_DIR, Bot
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.filters import CustomFilters
from bot.helper.ext_utils.menu_utils import Menus, rcloneListButtonMaker, rcloneListNextPage
from bot.helper.ext_utils.message_utils import editMessage, sendMarkup, sendMessage
from bot.helper.ext_utils.misc_utils import ButtonMaker, get_rclone_config, pairwise
from bot.helper.ext_utils.rclone_utils import is_not_config
from bot.helper.ext_utils.var_holder import get_rclone_var, set_rclone_var
from bot.helper.mirror_leech_utils.upload_utils.rclone.rclone_leech import RcloneLeech
from bot.modules.mirror import mirror_leech



async def handle_zip_leech_command(client, message):
    await leech(client, message, isZip=True)

async def handle_unzip_leech_command(client, message):
    await leech(client, message, extract=True)

async def handle_leech(client, message):
     await leech(client, message)

async def leech(client, message, isZip=False, extract=False):
    user_id= message.from_user.id
    if await is_not_config(user_id, message):
        return
    set_rclone_var('IS_ZIP', isZip, user_id)   
    set_rclone_var('EXTRACT', extract, user_id)  
    buttons= ButtonMaker()
    buttons.cb_buildbutton("🔗 From Link", f"leechselect^link^{user_id}")
    buttons.cb_buildbutton("📁 From Cloud", f"leechselect^cloud^{user_id}")
    buttons.cb_buildbutton("✘ Close Menu", f"leechselect^close^{user_id}")
    await sendMarkup("Select from where you want to leech", message, buttons.build_menu(2))  
    
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
        buttons.cb_buildsecbutton(f"📁 {j}", f"leechmenu^drive^{j}^{user_id}") 

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
        await editMessage("Select cloud where your files are stored", message, reply_markup= InlineKeyboardMarkup(buttons.first_button))
    else:
        await sendMarkup("Select cloud where your files are stored", message, reply_markup= InlineKeyboardMarkup(buttons.first_button))

async def list_dir(message, drive_name, drive_base, back= "back", edit=False):
    user_id= message.reply_to_message.from_user.id
    buttons = ButtonMaker()
    path = get_rclone_config(user_id)
    buttons.cbl_buildbutton("✅ Select this folder", f"leechmenu^leech_folder^{user_id}")

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
                callback = "dir",
                user_id= user_id)

        if offset == 0 and total <= 10:
            buttons.cbl_buildbutton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", data=f"leechmenu^pages^{user_id}")        
        else: 
            buttons.dbuildbutton(first_text= f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", first_callback=f"leechmenu^pages^{user_id}",
                                second_text= "NEXT ⏩", second_callback= f"next_leech {next_offset} {back}")

    buttons.cbl_buildbutton("⬅️ Back", data= f"leechmenu^{back}^{user_id}")
    buttons.cbl_buildbutton("✘ Close Menu", data=f"leechmenu^close^{user_id}")

    msg= 'Select folder or file that you want to leech\n'
    if get_rclone_var('IS_ZIP', user_id):
        msg= 'Select file that you want to zip\n' 
    if get_rclone_var('EXTRACT', user_id):
        msg= 'Select file that you want to extract\n'

    if edit:
        await editMessage(msg, message, reply_markup= InlineKeyboardMarkup(buttons.first_button))
    else:
        await sendMarkup(msg, message, reply_markup= InlineKeyboardMarkup(buttons.first_button))

async def leech_menu_cb(client, callback_query):
    query= callback_query
    data = query.data
    cmd = data.split("^")
    message = query.message
    user_id= query.from_user.id
    tag = f"@{message.reply_to_message.from_user.username}"
    base_dir= get_rclone_var("LEECH_BASE_DIR", user_id)
    rclone_drive = get_rclone_var("LEECH_DRIVE", user_id)
    is_zip = False
    extract = False

    if get_rclone_var('IS_ZIP', user_id):
        is_zip= True
        
    if get_rclone_var('EXTRACT', user_id):
        extract= True

    if cmd[1] == "pages":
        return await query.answer()

    if int(cmd[-1]) != user_id:
        return await query.answer("This menu is not for you!", show_alert=True)

    if cmd[1] == "drive":
        #Reset menu
        set_rclone_var("LEECH_BASE_DIR", "", user_id)
        base_dir= get_rclone_var("LEECH_BASE_DIR", user_id)

        drive_name= cmd[2]
        set_rclone_var("LEECH_DRIVE", drive_name, user_id)
        await list_dir(message, drive_name= drive_name, drive_base=base_dir, edit=True)
        await query.answer()   

    elif cmd[1] == "dir":
        path = get_rclone_var(cmd[2], user_id)
        base_dir += path + "/"
        set_rclone_var("LEECH_BASE_DIR", base_dir, user_id)
        await list_dir(message, drive_name= rclone_drive, drive_base=base_dir, edit=True)
        await query.answer()   

    elif cmd[1] == "leech_file":
        await query.answer()      
        path = get_rclone_var(cmd[2], user_id)
        base_dir += path
        dest_dir = f'{DOWNLOAD_DIR}{path}'
        rc_leech= RcloneLeech(message, user_id, base_dir, dest_dir, 
                             tag=tag, isZip=is_zip, extract=extract)
        await rc_leech.leech()
          
    elif cmd[1] == "leech_folder":
        await query.answer() 
        dest_dir = f'{DOWNLOAD_DIR}{base_dir}'
        rc_leech= RcloneLeech(message, user_id, base_dir, dest_dir, 
                              tag=tag, isZip=is_zip, extract=extract, isFolder=True)
        await rc_leech.leech()
          
    elif cmd[1] == "back":
        base_dir_split= base_dir.split("/")[:-2]
        base_dir_string = "" 
        for dir in base_dir_split: 
            base_dir_string += dir + "/"
        base_dir = base_dir_string
        set_rclone_var("LEECH_BASE_DIR", base_dir, user_id)
        
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
 
async def next_page_leech(client, callback_query):
    data = callback_query.data
    message= callback_query.message
    user_id= message.reply_to_message.from_user.id
    _, next_offset, data_back_cb= data.split()
    list_info = get_rclone_var("driveInfo", user_id)
    total = len(list_info)
    next_offset = int(next_offset)
    prev_offset = next_offset - 10 

    buttons = ButtonMaker()
    buttons.cbl_buildbutton(f"✅ Select this folder", f"leechmenu^leech_folder^{user_id}")

    next_list_info, _next_offset= rcloneListNextPage(list_info, next_offset)

    rcloneListButtonMaker(result_list= next_list_info,
        buttons=buttons,
        menu_type= Menus.LEECH, 
        callback = "dir",
        user_id= user_id)

    if next_offset == 0:
        buttons.dbuildbutton(first_text = f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", first_callback="leechmenu^pages", 
                            second_text= "NEXT ⏩", second_callback= f"next_leech {_next_offset} {data_back_cb}" )
    
    elif next_offset >= total:
        buttons.dbuildbutton(first_text="⏪ BACK", first_callback= f"next_leech {prev_offset} {data_back_cb}", 
                        second_text=f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", second_callback="leechmenu^pages")
   
    elif next_offset + 10 > total:
        buttons.dbuildbutton(first_text="⏪ BACK", first_callback= f"next_leech {prev_offset} {data_back_cb}", 
                        second_text= f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", second_callback="leechmenu^pages")                               
    else:
        buttons.tbuildbutton(first_text="⏪ BACK", first_callback= f"next_leech {prev_offset} {data_back_cb}", 
                            second_text= f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", second_callback="leechmenu^pages",
                            third_text="NEXT ⏩", third_callback=f"next_leech {_next_offset} {data_back_cb}")

    buttons.cbl_buildbutton("⬅️ Back", f"leechmenu^{data_back_cb}^{user_id}")
    buttons.cbl_buildbutton("✘ Close Menu", f"leechmenu^close^{user_id}")

    leech_drive= get_rclone_var("LEECH_DRIVE", user_id)
    base_dir= get_rclone_var("LEECH_BASE_DIR", user_id)
    await editMessage(f"Select folder or file that you want to leech\n\nPath:`{leech_drive}:{base_dir}`", message, 
                        reply_markup= InlineKeyboardMarkup(buttons.first_button))    
           
async def selection_callback(client, callback_query):
    query= callback_query
    data = query.data
    cmd = data.split("^")
    message = query.message
    user_id= query.from_user.id
    is_zip = get_rclone_var("IS_ZIP", user_id)
    extract = get_rclone_var("EXTRACT", user_id)

    if int(cmd[-1]) != user_id:
        return await query.answer("This menu is not for you!", show_alert=True)

    if cmd[1] == "link":
        await query.answer()     
        question= await sendMessage("Send link to leech, /ignore to cancel", message)
        try:
            response = await client.listen.Message(filters.text, id=filters.user(user_id), timeout= 30)
        except asyncio.TimeoutError:
            await sendMessage("Too late 30s gone, try again!", message)
        else:
            if response:
                try:
                    if "/ignore" in response.text:
                        await client.listen.Cancel(filters.user(user_id))
                    else:
                        link= response.text
                        await mirror_leech(client, message, _link= link, isZip= is_zip, extract= extract, isLeech=True, from_cb=True)
                except Exception as ex:
                        await sendMessage(str(ex), message) 
        finally:
            await question.delete()
    
    if cmd[1] == "cloud":
        await list_drive(message, edit=True)
        await query.answer()
    
    elif cmd[1] == "close":
        await query.answer("Closed")
        await message.delete()


next_page_cb= CallbackQueryHandler(next_page_leech, filters= regex("next_leech"))
leech_callback= CallbackQueryHandler(leech_menu_cb, filters= regex("leechmenu"))
selection_cb= CallbackQueryHandler(selection_callback, filters= regex("leechselect"))
leech_handler = MessageHandler(handle_leech, filters= command(BotCommands.LeechCommand) & CustomFilters.user_filter | CustomFilters.chat_filter)
zip_leech_handler = MessageHandler(handle_zip_leech_command, filters= command(BotCommands.ZipLeechCommand) & CustomFilters.user_filter | CustomFilters.chat_filter)
unzip_leech_handler = MessageHandler(handle_unzip_leech_command, filters= command(BotCommands.UnzipLeechCommand) & CustomFilters.user_filter | CustomFilters.chat_filter)

Bot.add_handler(next_page_cb)
Bot.add_handler(leech_callback)
Bot.add_handler(selection_cb)
Bot.add_handler(leech_handler)
Bot.add_handler(zip_leech_handler)
Bot.add_handler(unzip_leech_handler)