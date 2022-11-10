from configparser import ConfigParser
from asyncio.subprocess import PIPE, create_subprocess_exec as exec
from pyrogram.filters import regex
from pyrogram import filters
from pyrogram.handlers import CallbackQueryHandler, MessageHandler
from bot import LOGGER, bot
from json import loads as jsonloads
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.filters import CustomFilters
from bot.helper.ext_utils.menu_utils import Menus, rcloneListButtonMaker, rcloneListNextPage
from bot.helper.ext_utils.message_utils import editMessage, sendMarkup, sendMessage
from bot.helper.ext_utils.misc_utils import ButtonMaker, get_rclone_config
from bot.helper.ext_utils.rclone_utils import is_rclone_config
from bot.helper.ext_utils.var_holder import get_rclone_val, update_rclone_var
from bot.modules.myfilesset import calculate_size, delete_selected, delete_selection, myfiles_settings, rclone_dedupe, rclone_mkdir, rclone_rename



async def handle_myfiles(client, message):
    if await is_rclone_config(message.from_user.id, message):
        await list_remotes(message)

async def list_remotes(message, edit=False):
    if message.reply_to_message:
        user_id= message.reply_to_message.from_user.id
    else:
        user_id= message.from_user.id

    buttons = ButtonMaker()
    path= get_rclone_config(user_id)
    conf = ConfigParser()
    conf.read(path)
    for remote in conf.sections():
        buttons.cb_buildbutton(f"📁 {remote}", f"myfilesmenu^drive^{remote}^{user_id}")

    buttons.cb_buildbutton("✘ Close Menu", f"myfilesmenu^close^{user_id}", 'footer')

    if edit:
        await editMessage("Select your cloud to list files", message, reply_markup= buttons.build_menu(2))
    else:
        await sendMarkup("Select your cloud to list files", message, reply_markup= buttons.build_menu(2))

async def list_folder(message, drive_name, drive_base, edit=False):
    user_id= message.reply_to_message.from_user.id
    buttons = ButtonMaker()
    path = get_rclone_config(user_id)
    buttons.cb_buildbutton(f"⚙️ Folder Options", f"myfilesmenu^folder_actions^{user_id}")

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
    update_rclone_var("driveInfo", list_info, user_id)

    if len(list_info) == 0:
        buttons.cb_buildbutton("❌Nothing to show❌", f"myfilesmenu^pages^{user_id}")   
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
            buttons.cb_buildbutton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", "myfilesmenu^pages", 'footer') 
        else: 
            buttons.cb_buildbutton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", "myfilesmenu^pages", 'footer')
            buttons.cb_buildbutton("NEXT ⏩", f"next_myfiles {next_offset} back", 'footer')   

    buttons.cb_buildbutton(f"⬅️ Back", f"myfilesmenu^back^{user_id}", 'footer_second')
    buttons.cb_buildbutton("✘ Close Menu", f"myfilesmenu^close^{user_id}", 'footer_second')

    msg= f"Your cloud files are listed below\n\n<b>Path:</b><code>{drive_name}:{drive_base}</code>"

    if edit:
        await editMessage(msg, message, reply_markup= buttons.build_menu(1))
    else:
        await sendMarkup(msg, message, reply_markup= buttons.build_menu(1))

async def myfiles_callback(client, callback_query):
    query= callback_query
    data = query.data
    cmd = data.split("^")
    message = query.message
    tag = f"@{message.reply_to_message.from_user.username}"
    user_id= query.from_user.id
    base_dir= get_rclone_val("MYFILES_BASE_DIR", user_id)
    rclone_drive = get_rclone_val("MYFILES_DRIVE", user_id)

    if cmd[1] == "pages":
        return await query.answer()

    if int(cmd[-1]) != user_id:
        return await query.answer("This menu is not for you!", show_alert=True)

    if cmd[1] == "drive":
        #Reset Menu
        update_rclone_var("MYFILES_BASE_DIR", "", user_id)
        base_dir= get_rclone_val("MYFILES_BASE_DIR", user_id)
             
        drive_name= cmd[2]  
        update_rclone_var("MYFILES_DRIVE", drive_name, user_id)
        await list_folder(message, drive_name= drive_name, drive_base=base_dir, edit=True)
        await query.answer() 

    elif cmd[1] == "dir":
        path = get_rclone_val(cmd[2], user_id)
        base_dir += path + "/"
        update_rclone_var("MYFILES_BASE_DIR", base_dir, user_id)
        await list_folder(message, drive_name= rclone_drive, drive_base=base_dir, edit=True)
        await query.answer()

    # Handle back button
    elif cmd[1] == "back":
        if len(base_dir) == 0: 
            await list_remotes(message, edit=True)
            await query.answer()
            return 
        base_dir_split= base_dir.split("/")[:-2]
        base_dir_string = "" 
        for dir in base_dir_split: 
            base_dir_string += dir + "/"
        base_dir = base_dir_string
        update_rclone_var("MYFILES_BASE_DIR", base_dir, user_id)
        await list_folder(message, drive_name= rclone_drive, drive_base=base_dir, edit=True)
        await query.answer()

    elif cmd[1] == "back_remotes_menu":
        await list_remotes(message, edit=True)
        await query.answer()
        
    #Handle actions
    elif cmd[1] == "file_actions":
        path = get_rclone_val(cmd[2], user_id)
        base_dir += path
        update_rclone_var("MYFILES_BASE_DIR", base_dir, user_id) 
        await myfiles_settings(message, rclone_drive, base_dir, edit=True, is_folder=False) 
        await query.answer()

    elif cmd[1] == "folder_actions":
        await myfiles_settings(message, rclone_drive, base_dir, edit=True, is_folder=True)
        await query.answer()

    if cmd[1] == "delete_action":
        if cmd[2] == "folder":
            is_folder= True
        elif cmd[2] == "file":
            is_folder= False
        await delete_selection(message, user_id, is_folder=is_folder)
        await query.answer()

    elif cmd[1] == "size_action":
        await calculate_size(message, base_dir, rclone_drive, user_id)
        await query.answer()

    elif cmd[1] == "mkdir_action":
        await rclone_mkdir(client, query, message, rclone_drive, base_dir, tag)

    elif cmd[1] == "dedupe_action":
        await query.answer()     
        await rclone_dedupe(message, rclone_drive, base_dir, user_id, tag)

    elif cmd[1] == "rename_action":
        await query.answer()     
        await rclone_rename(client, message, rclone_drive, base_dir, tag)

    if cmd[1]== "yes":
        if cmd[2] == "folder":
            is_folder= True
        elif cmd[2] == "file":
            is_folder= False
        await delete_selected(message, user_id, base_dir , rclone_drive, is_folder=is_folder)
        await query.answer()
        
    elif cmd[1]== "no":
        await query.answer() 
        await message.delete()
    
    if cmd[1] == "close":
        await query.answer()
        await message.delete()

async def next_page_myfiles(client, callback_query):
    query= callback_query
    data= query.data
    message= query.message
    await query.answer()
    user_id= message.reply_to_message.from_user.id
    _, next_offset, data_back_cb = data.split()
    list_info = get_rclone_val("driveInfo", user_id)
    total = len(list_info)
    next_offset = int(next_offset)
    prev_offset = next_offset - 10 

    buttons = ButtonMaker()
    buttons.cb_buildbutton(f"⚙️ Folder Options", f"myfilesmenu^folder_actions^{user_id}")

    next_list_info, _next_offset= rcloneListNextPage(list_info, next_offset)

    rcloneListButtonMaker(result_list= next_list_info,
        buttons= buttons,
        menu_type= Menus.MYFILES, 
        callback = "dir",
        user_id= user_id)

    if next_offset == 0:
        buttons.cb_buildbutton(f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", "myfilesmenu^pages", 'footer')
        buttons.cb_buildbutton("NEXT ⏩", f"next_myfiles {_next_offset} {data_back_cb}", 'footer')

    elif next_offset >= total:
        buttons.cb_buildbutton("⏪ BACK", f"next_myfiles {prev_offset} {data_back_cb}", 'footer')
        buttons.cb_buildbutton(f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", "myfilesmenu^pages", 'footer')

    elif next_offset + 10 > total:
        buttons.cb_buildbutton("⏪ BACK", f"next_myfiles {prev_offset} {data_back_cb}", 'footer')                               
        buttons.cb_buildbutton(f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}","myfilesmenu^pages", 'footer')
    else:
        buttons.cb_buildbutton("⏪ BACK", f"next_myfiles {prev_offset} {data_back_cb}", 'footer_second')
        buttons.cb_buildbutton(f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", "myfilesmenu^pages", 'footer')
        buttons.cb_buildbutton("NEXT ⏩", f"next_myfiles {_next_offset} {data_back_cb}", 'footer_second')

    buttons.cb_buildbutton("⬅️ Back", f"myfilesmenu^{data_back_cb}^{user_id}", 'footer_third')
    buttons.cb_buildbutton("✘ Close Menu", f"myfilesmenu^close^{user_id}", 'footer_third')

    myfiles_drive= get_rclone_val("MYFILES_DRIVE", user_id)
    base_dir= get_rclone_val("MYFILES_BASE_DIR", user_id)
    await editMessage(f"Your cloud files are listed below\n\n<b>Path:</b><code>{myfiles_drive}:{base_dir}</code>", message, 
                      reply_markup= buttons.build_menu(1))


myfiles_handler = MessageHandler(handle_myfiles, filters= filters.command(BotCommands.MyFilesCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter))
next_page_myfiles_cb= CallbackQueryHandler(next_page_myfiles, filters= regex("next_myfiles"))
myfiles_cb = CallbackQueryHandler(myfiles_callback, filters= regex("myfilesmenu"))

bot.add_handler(myfiles_cb)
bot.add_handler(next_page_myfiles_cb)
bot.add_handler(myfiles_handler)