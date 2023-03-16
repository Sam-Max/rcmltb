from configparser import ConfigParser
from asyncio.subprocess import PIPE, create_subprocess_exec as exec
from json import loads as jsonloads
from bot import LOGGER, bot, config_dict
from pyrogram.filters import regex, command
from pyrogram.handlers import CallbackQueryHandler, MessageHandler
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.filters import CustomFilters
from bot.helper.ext_utils.menu_utils import Menus, rcloneListButtonMaker, rcloneListNextPage
from bot.helper.ext_utils.message_utils import deleteMessage, editMessage, sendMarkup, sendMessage
from bot.helper.ext_utils.button_build import ButtonMaker
from bot.helper.ext_utils.rclone_utils import get_rclone_config, is_rclone_config
from bot.helper.ext_utils.rclone_data_holder import get_rclone_data, update_rclone_data
from bot.helper.mirror_leech_utils.download_utils.rclone_copy import RcloneCopy
from bot.modules.listener import MirrorLeechListener


listener_dict = {}



async def handle_copy(client, message):
    user_id= message.from_user.id
    message_id= message.id
    tag = f"@{message.from_user.username}"
    if await is_rclone_config(user_id, message):
        origin_remote = get_rclone_data("COPY_ORIGIN_REMOTE", user_id)      
        origin_dir= get_rclone_data("COPY_ORIGIN_DIR", user_id)
        listener= MirrorLeechListener(message, tag, user_id)
        listener_dict[message_id] = [listener]
        if config_dict['MULTI_RCLONE_CONFIG'] or CustomFilters._owner_query(user_id): 
            await list_remotes(message, callback="remote_origin", rclone_drive=origin_remote, base_dir=origin_dir)
        else:
            await sendMessage("Not allowed to use", message)

async def list_remotes(message, callback, rclone_drive, base_dir, is_second_menu=False, edit=False):
    if message.reply_to_message:
        user_id= message.reply_to_message.from_user.id
    else:
        user_id= message.from_user.id
    buttons = ButtonMaker()
    path= get_rclone_config(user_id)
    conf = ConfigParser()
    conf.read(path)
    for remote in conf.sections():
        buttons.cb_buildbutton(f"📁 {remote}", f"copymenu^{callback}^{remote}^{user_id}")
    if is_second_menu:
        msg = 'Select folder where you want to copy' 
    else:
        if rclone_drive and base_dir:
            msg = f"Select cloud where your files are stored\n\n<b>Path: </b><code>{rclone_drive}:{base_dir}</code>"
        else:
            msg = f"Select cloud where your files are stored\n\n"
    buttons.cb_buildbutton("✘ Close Menu", f"copymenu^close^{user_id}", 'footer')
    if edit:
        await editMessage(msg, message, reply_markup= buttons.build_menu(2))
    else:
        await sendMarkup(msg, message, reply_markup= buttons.build_menu(2))

async def list_folder(message, drive_name, drive_base, dir_callback, back_callback, edit=False, is_second_menu=False):
        user_id= message.reply_to_message.from_user.id
        conf_path = get_rclone_config(user_id)
        buttons = ButtonMaker()

        if is_second_menu:
            file_callback = 'copy'
            buttons.cb_buildbutton(f"✅ Select this folder", f"copymenu^copy^{user_id}")
            cmd = ["rclone", "lsjson", f'--config={conf_path}', f"{drive_name}:{drive_base}", "--dirs-only"] 
        else:
            file_callback = 'second_menu'
            buttons.cb_buildbutton(f"✅ Select this folder", f"copymenu^second_menu^_^False^{user_id}")
            cmd = ["rclone", "lsjson", f'--config={conf_path}', f"{drive_name}:{drive_base}"] 

        process = await exec(*cmd, stdout=PIPE, stderr=PIPE)
        out, err = await process.communicate()
        out = out.decode().strip()
        return_code = await process.wait()
        if return_code != 0:
           err = err.decode().strip()
           return await sendMessage(f'Error: {err}', message)

        list_info = jsonloads(out)
        if is_second_menu:
            list_info.sort(key=lambda x: x["Name"]) 
        else:
            list_info.sort(key=lambda x: x["Size"])  
        
        update_rclone_data("list_info", list_info, user_id)
        
        if len(list_info) == 0:
            buttons.cb_buildbutton("❌Nothing to show❌", "copymenu^pages^{user_id}")
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
                buttons= buttons, 
                menu_type = Menus.COPY,
                dir_callback= dir_callback,
                file_callback= file_callback,
                user_id= user_id)

            if offset == 0 and total <= 10:
                buttons.cb_buildbutton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", "copymenu^pages^{user_id}", 'footer') 
            else: 
                buttons.cb_buildbutton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", "copymenu^pages^{user_id}", 'footer')
                buttons.cb_buildbutton("NEXT ⏩", f"next_copy {next_offset} {is_second_menu} {back_callback}", 'footer')

        buttons.cb_buildbutton("⬅️ Back", f"copymenu^{back_callback}^{user_id}", 'footer_second')
        buttons.cb_buildbutton("✘ Close Menu", f"copymenu^close^{user_id}", 'footer_second')

        if is_second_menu:
            msg=f'Select folder where you want to copy\n\n<b>Path: </b><code>{drive_name}:{drive_base}</code>'
        else:    
            msg= f'Select file or folder which you want to copy\n\n<b>Path: </b><code>{drive_name}:{drive_base}</code>'

        if edit:
            await editMessage(msg, message, reply_markup= buttons.build_menu(1))
        else:
            await sendMarkup(msg, message, reply_markup= buttons.build_menu(1))

async def copy_menu_callback(client, callback_query):
    query= callback_query
    data = query.data
    cmd = data.split("^")
    message = query.message
    user_id= query.from_user.id
    msg_id= message.reply_to_message.id
    listener= listener_dict[msg_id][0]
    origin_remote = get_rclone_data("COPY_ORIGIN_REMOTE", user_id)
    origin_dir= get_rclone_data("COPY_ORIGIN_DIR", user_id)
    dest_remote= get_rclone_data("COPY_DESTINATION_REMOTE", user_id)
    dest_dir= get_rclone_data("COPY_DESTINATION_DIR", user_id)

    if int(cmd[-1]) != user_id:
        await query.answer("This menu is not for you!", show_alert=True)
    #First Menu
    elif cmd[1] == "remote_origin":
        #Clean Menu
        update_rclone_data("COPY_ORIGIN_DIR", "", user_id)
        origin_dir= get_rclone_data("COPY_ORIGIN_DIR", user_id)
        update_rclone_data("COPY_ORIGIN_REMOTE", cmd[2], user_id)
        await list_folder(message, drive_name= cmd[2], drive_base= origin_dir, dir_callback="origin_dir", back_callback= "back_origin", edit=True)
        await query.answer()
    elif cmd[1] == "origin_dir":
        path = get_rclone_data(cmd[2], user_id)
        origin_dir_= origin_dir + path  + "/"
        update_rclone_data("COPY_ORIGIN_DIR", origin_dir_, user_id)
        await list_folder(message, drive_name= origin_remote, drive_base= origin_dir_, dir_callback="origin_dir", back_callback= "back_origin", edit=True)
        await query.answer()     
    #Second Menu
    elif cmd[1] == "second_menu":
        if cmd[3] == "True":
            path = get_rclone_data(cmd[2], user_id)
            origin_dir_= origin_dir + path  
            update_rclone_data("COPY_ORIGIN_DIR", origin_dir_, user_id)
        await list_remotes(message, callback="remote_dest", rclone_drive= dest_remote, base_dir= dest_dir, edit=True, is_second_menu=True)   
        await query.answer()   
    elif cmd[1] == "remote_dest":
        #Clean Menu
        update_rclone_data("COPY_DESTINATION_DIR", "", user_id)
        dest_dir= get_rclone_data("COPY_DESTINATION_DIR", user_id) 
        dest_remote= cmd[2]
        update_rclone_data("COPY_DESTINATION_REMOTE", dest_remote, user_id)
        await list_folder(message, drive_name= dest_remote, drive_base= dest_dir, dir_callback="dir_dest", edit=True, back_callback= "back_dest", is_second_menu=True)
        await query.answer() 
    elif cmd[1] == "dir_dest":
        path = get_rclone_data(cmd[2], user_id)
        dest_dir_= f"{dest_dir}{path}/"
        update_rclone_data("COPY_DESTINATION_DIR", dest_dir_, user_id)
        await list_folder(message, drive_name= dest_remote, drive_base= dest_dir_, dir_callback="dir_dest", edit=True, back_callback= "back_dest", is_second_menu=True)
        await query.answer()     
    elif cmd[1] == "copy":
        await query.answer()      
        await deleteMessage(message)
        rclone_copy= RcloneCopy(user_id, listener)
        await rclone_copy.copy(origin_remote, origin_dir, dest_remote, dest_dir)
    elif cmd[1] == "pages":
        await query.answer()
    elif cmd[1] == "close":
        await query.answer()
        await message.delete()
    # Origin Menu Back Button
    if cmd[1] == "back_origin":
        if len(origin_dir) == 0:
            await query.answer() 
            await list_remotes(message, callback="remote_origin", rclone_drive= dest_remote, base_dir= dest_dir, edit=True) 
            return
        origin_dir_list= origin_dir.split("/")[:-2]
        origin_dir_string = "" 
        for dir in origin_dir_list: 
            origin_dir_string += dir + "/" 
        origin_dir= origin_dir_string
        update_rclone_data("COPY_ORIGIN_DIR", origin_dir, user_id)
        await list_folder(message, drive_name= origin_remote, drive_base= origin_dir, dir_callback="origin_dir", edit=True, back_callback= cmd[1])
        await query.answer() 
    # Destination Menu Back Button
    elif cmd[1] == "back_dest":
        if len(dest_dir) == 0:
            await query.answer() 
            await list_remotes(message, callback="remote_dest", rclone_drive= dest_remote, base_dir= dest_dir, edit=True, is_second_menu=True)             
            return
        dest_dir_list= dest_dir.split("/")[:-2]
        dest_dir_string = "" 
        for dir in dest_dir_list: 
            dest_dir_string += dir + "/"
        dest_dir= dest_dir_string
        update_rclone_data("COPY_DESTINATION_DIR", dest_dir, user_id)
        await list_folder(message, drive_name= dest_remote, drive_base= dest_dir, dir_callback="dir_dest", edit=True, back_callback= cmd[1] , is_second_menu=True)
        await query.answer() 

async def next_page_copy(client, callback_query):
    query= callback_query
    data= query.data
    message= query.message
    await query.answer()
    user_id= message.reply_to_message.from_user.id
    _, next_offset, is_second_menu, data_back_cb = data.split()
    is_second_menu = is_second_menu.lower() == 'true'
    
    list_info = get_rclone_data("list_info", user_id)
    total = len(list_info)
    next_offset = int(next_offset)
    prev_offset = next_offset - 10 
    buttons = ButtonMaker()
    next_list_info, _next_offset= rcloneListNextPage(list_info, next_offset) 

    if is_second_menu:
        dir_callback= "dir_dest"
        file_callback= 'copy'
        buttons.cb_buildbutton("✅ Select this folder", f"copymenu^copy^{user_id}")
    else:
        dir_callback= "origin_dir"
        file_callback= 'second_menu'
        buttons.cb_buildbutton("✅ Select this folder", f"copymenu^second_menu^_^False^{user_id}")
    
    rcloneListButtonMaker(result_list= next_list_info, 
        buttons= buttons,
        menu_type= Menus.COPY,
        dir_callback= dir_callback,
        file_callback= file_callback,
        user_id= user_id)

    if next_offset == 0:
        buttons.cb_buildbutton(f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", "copymenu^pages", 'footer')
        buttons.cb_buildbutton("NEXT ⏩", f"next_copy {_next_offset} {is_second_menu} {data_back_cb}", 'footer')
    
    elif next_offset >= total:
        buttons.cb_buildbutton("⏪ BACK", f"next_copy {prev_offset} {is_second_menu} {data_back_cb}", 'footer')
        buttons.cb_buildbutton(f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", "setting pages", 'footer')

    elif next_offset + 10 > total:
        buttons.cb_buildbutton("⏪ BACK", f"next_copy {prev_offset} {is_second_menu} {data_back_cb}", 'footer') 
        buttons.cb_buildbutton(f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", "copymenu^pages", 'footer')                              
    else:
        buttons.cb_buildbutton("⏪ BACK", f"next_copy {prev_offset} {is_second_menu} {data_back_cb}", 'footer_second')
        buttons.cb_buildbutton(f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", "copymenu^pages", 'footer')
        buttons.cb_buildbutton("NEXT ⏩", f"next_copy {_next_offset} {is_second_menu} {data_back_cb}", 'footer_second')

    buttons.cb_buildbutton("⬅️ Back", f"copymenu^{data_back_cb}^{user_id}", 'footer_third')
    buttons.cb_buildbutton("✘ Close Menu", f"copymenu^close^{user_id}", 'footer_third')
                            
    if is_second_menu:
        dest_remote= get_rclone_data("COPY_DESTINATION_REMOTE", user_id)
        dest_dir= get_rclone_data("COPY_DESTINATION_DIR", user_id)
        await editMessage(f"Select folder where you want to copy\n\nPath:<code>{dest_remote}:{dest_dir}</code>", 
                          message, reply_markup= buttons.build_menu(1))
    else:
        origin_remote= get_rclone_data("COPY_ORIGIN_REMOTE", user_id)
        origin_dir= get_rclone_data("COPY_ORIGIN_DIR", user_id)
        await editMessage(f"Select file or folder which you want to copy\n\nPath:<code>{origin_remote}:{origin_dir}</code>", 
                          message, reply_markup= buttons.build_menu(1))


copy_handler = MessageHandler(handle_copy, filters= command(BotCommands.CopyCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter))
next_page_cb= CallbackQueryHandler(next_page_copy, filters= regex("next_copy"))
copy_menu_cb= CallbackQueryHandler(copy_menu_callback, filters= regex("copymenu"))

bot.add_handler(copy_handler)
bot.add_handler(next_page_cb)
bot.add_handler(copy_menu_cb)