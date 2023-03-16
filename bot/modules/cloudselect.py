from asyncio.subprocess import PIPE, create_subprocess_exec as exec
from configparser import ConfigParser
from bot import LOGGER, OWNER_ID, bot, config_dict, remotes_data
from json import loads as jsonloads
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.filters import CustomFilters
from bot.helper.ext_utils.menu_utils import Menus, rcloneListButtonMaker, rcloneListNextPage
from bot.helper.ext_utils.message_utils import editMessage, sendMarkup, sendMessage
from bot.helper.ext_utils.button_build import ButtonMaker
from bot.helper.ext_utils.rclone_utils import get_rclone_config, is_rclone_config
from bot.helper.ext_utils.rclone_data_holder import get_rclone_data, update_rclone_data
from pyrogram.filters import regex
from pyrogram import filters
from pyrogram.handlers import CallbackQueryHandler, MessageHandler




async def handle_cloudselect(client, message):
    user_id= message.from_user.id
    if await is_rclone_config(user_id, message):
        if DEFAULT_OWNER_REMOTE := config_dict['DEFAULT_OWNER_REMOTE']:
            if user_id == OWNER_ID:
                update_rclone_data("CLOUDSEL_REMOTE", DEFAULT_OWNER_REMOTE, user_id)
        rclone_remote = get_rclone_data("CLOUDSEL_REMOTE", user_id)              
        base_dir= get_rclone_data("CLOUDSEL_BASE_DIR", user_id)
        if config_dict['MULTI_RCLONE_CONFIG'] or CustomFilters._owner_query(user_id): 
            await list_remotes(message, rclone_remote, base_dir) 
        else:
            await sendMessage("Not allowed to use", message)        

async def list_remotes(message, rclone_remote, base_dir, edit=False):
    if message.reply_to_message:
        user_id= message.reply_to_message.from_user.id
    else:
        user_id= message.from_user.id
    buttons = ButtonMaker()
    path= get_rclone_config(user_id)
    conf = ConfigParser()
    conf.read(path)
    for remote in conf.sections():
        prev = ""
        if config_dict['MULTI_REMOTE_UP'] and user_id== OWNER_ID:
            if remote in remotes_data: 
                prev = "✅"
        else:
            if remote == get_rclone_data("CLOUDSEL_REMOTE", user_id): 
                prev = "✅"
        buttons.cb_buildbutton(f"{prev} 📁 {remote}", f"cloudselectmenu^remote^{remote}^{user_id}")
    if config_dict['MULTI_REMOTE_UP']:
        buttons.cb_buildbutton("🔄 Reset", f"cloudselectmenu^reset^{user_id}", 'footer')
    buttons.cb_buildbutton("✘ Close Menu", f"cloudselectmenu^close^{user_id}", 'footer')
    if config_dict['MULTI_REMOTE_UP']:
        msg= f"Select all clouds where you want to upload file"
    else:
        if rclone_remote and base_dir:
            msg= f"Select cloud where you want to upload file\n\n<b>Path:</b><code>{rclone_remote}:{base_dir}</code>"
        else:
            msg= f"Select cloud where you want to upload file\n\n"
    if edit:
        await editMessage(msg, message, reply_markup= buttons.build_menu(2))
    else:
        await sendMarkup(msg, message, reply_markup= buttons.build_menu(2))
    
async def list_folder(message, remote_name, remote_base, edit=False):
    user_id= message.reply_to_message.from_user.id
    buttons = ButtonMaker()
    path = get_rclone_config(user_id)
    buttons.cb_buildbutton(f"✅ Select this folder", f"cloudselectmenu^close^{user_id}")
    
    cmd = ["rclone", "lsjson", '--dirs-only', f'--config={path}', f"{remote_name}:{remote_base}" ] 
    process = await exec(*cmd, stdout=PIPE, stderr=PIPE)
    out, err = await process.communicate()
    out = out.decode().strip()
    return_code = await process.wait()
    if return_code != 0:
        err = err.decode().strip()
        return await sendMessage(f'Error: {err}', message)
    list_info = jsonloads(out)
    list_info.sort(key=lambda x: x["Size"])
    update_rclone_data("list_info", list_info, user_id)
    
    if len(list_info) == 0:
        buttons.cb_buildbutton("❌Nothing to show❌", "cloudselectmenu^pages^{user_id}")
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
            menu_type= Menus.CLOUDSEL, 
            dir_callback = "remote_dir",
            file_callback= "",
            user_id= user_id)
        if offset == 0 and total <= 10:
            buttons.cb_buildbutton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", f"cloudselectmenu^pages^{user_id}", 'footer') 
        else:
            buttons.cb_buildbutton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", f"cloudselectmenu^pages^{user_id}", 'footer')
            buttons.cb_buildbutton("NEXT ⏩", f"next_cloudselect {next_offset} back", 'footer')

    buttons.cb_buildbutton("⬅️ Back", f"cloudselectmenu^back^{user_id}", 'footer_second')
    buttons.cb_buildbutton("✘ Close Menu", f"cloudselectmenu^close^{user_id}", 'footer_second')

    msg= f"Select folder where you want to store files\n\n<b>Path:</b><code>{remote_name}:{remote_base}</code>"
    if edit:
        await editMessage(msg, message, reply_markup= buttons.build_menu(1))
    else:
        await sendMarkup(msg, message, reply_markup= buttons.build_menu(1))

async def cloudselect_callback(client, callback_query):
    query= callback_query
    data = query.data
    cmd = data.split("^")
    message = query.message
    user_id= query.from_user.id
    base_dir= get_rclone_data("CLOUDSEL_BASE_DIR", user_id)
    rclone_remote = get_rclone_data("CLOUDSEL_REMOTE", user_id)

    if int(cmd[-1]) != user_id:
        return await query.answer("This menu is not for you!", show_alert=True)
    elif cmd[1] == "remote":
        if config_dict['MULTI_REMOTE_UP'] and user_id== OWNER_ID:
            remotes_data.append(cmd[2])
            await list_remotes(message, cmd[2], "", edit=True)
        else:
            update_rclone_data("CLOUDSEL_BASE_DIR", "/", user_id) #Reset Dir
            update_rclone_data("CLOUDSEL_REMOTE", cmd[2], user_id)
            if user_id == OWNER_ID:
                config_dict.update({'DEFAULT_OWNER_REMOTE': cmd[2]}) 
            await list_folder(message, remote_name= cmd[2], remote_base="/", edit=True)
            await query.answer()
    elif cmd[1] == "remote_dir":
        path = get_rclone_data(cmd[2], user_id)
        base_dir += path + "/"
        update_rclone_data("CLOUDSEL_BASE_DIR", base_dir, user_id)
        await list_folder(message, remote_name= rclone_remote, remote_base=base_dir, edit=True)
        await query.answer()
    elif cmd[1] == "back":
        if len(base_dir) == 0: 
            await query.answer() 
            await list_remotes(message, "", "", edit=True)
            return 
        base_dir_split= base_dir.split("/")[:-2]
        base_dir_string = "" 
        for dir in base_dir_split: 
            base_dir_string += dir + "/"
        base_dir = base_dir_string
        update_rclone_data("CLOUDSEL_BASE_DIR", base_dir, user_id)
        await list_folder(message, remote_name= rclone_remote, remote_base=base_dir, edit=True)
        await query.answer() 
    elif cmd[1] == "pages":
        await query.answer()
    elif cmd[1] == "reset":
        remotes_data.clear()
        await list_remotes(message, "", "", edit=True)
    else:
        await query.answer()
        await message.delete()

async def next_page_cloudselect(client, callback_query):
    query= callback_query
    data= query.data
    message= query.message
    await query.answer()
    user_id= message.reply_to_message.from_user.id
    _, next_offset, data_back_cb = data.split()
    list_info = get_rclone_data("list_info", user_id)
    total = len(list_info)
    next_offset = int(next_offset)
    prev_offset = next_offset - 10 

    buttons = ButtonMaker()
    buttons.cb_buildbutton("✅ Select this folder", f"cloudselectmenu^close^{user_id}")

    next_list_info, _next_offset= rcloneListNextPage(list_info, next_offset) 
    rcloneListButtonMaker(result_list= next_list_info, 
        buttons= buttons,
        menu_type= Menus.CLOUDSEL,
        dir_callback = "remote_dir",
        file_callback= "",
        user_id= user_id)

    if next_offset == 0:
        buttons.cb_buildbutton(f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", "cloudselectmenu^pages", 'footer')
        buttons.cb_buildbutton("NEXT ⏩", f"next_cloudselect {_next_offset} {data_back_cb}", 'footer')

    elif next_offset >= total:
        buttons.cb_buildbutton("⏪ BACK", f"next_cloudselect {prev_offset} {data_back_cb}", 'footer')
        buttons.cb_buildbutton(f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", "cloudselectmenu^pages", 'footer')

    elif next_offset + 10 > total:
        buttons.cb_buildbutton("⏪ BACK", f"next_cloudselect {prev_offset} {data_back_cb}", 'footer')                              
        buttons.cb_buildbutton(f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", "cloudselectmenu^pages", 'footer')
    else:
        buttons.cb_buildbutton("⏪ BACK", f"next_cloudselect{prev_offset} {data_back_cb}", 'footer_second')
        buttons.cb_buildbutton(f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", "cloudselectmenu^pages", 'footer')
        buttons.cb_buildbutton("NEXT ⏩", f"next_cloudselect{_next_offset} {data_back_cb}", 'footer_second')

    buttons.cb_buildbutton("⬅️ Back", f"cloudselectlmenu^{data_back_cb}^{user_id}", 'footer_third')
    buttons.cb_buildbutton("✘ Close Menu", f"cloudselectmenu^close^{user_id}", 'footer_third')

    cloudselect_remote= get_rclone_data("CLOUDSEL_REMOTE", user_id)
    base_dir= get_rclone_data("CLOUDSEL_BASE_DIR", user_id)
    await editMessage(f"Select folder where you want to store files\n\n<b>Path:</b><code>{cloudselect_remote}:{base_dir}</code>", message, reply_markup= buttons.build_menu(1))
 
 
cloudselect_handler = MessageHandler(handle_cloudselect, filters= filters.command(BotCommands.CloudSelectCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter))
next_cloudselect_cb= CallbackQueryHandler(next_page_cloudselect, filters= regex("next_cloudselect"))
cloudselect_cb = CallbackQueryHandler(cloudselect_callback, filters= regex("cloudselectmenu"))

bot.add_handler(cloudselect_cb)
bot.add_handler(next_cloudselect_cb)
bot.add_handler(cloudselect_handler)