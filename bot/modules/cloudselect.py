from bot import OWNER_ID, bot, config_dict, remotes_multi
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.filters import CustomFilters
from bot.helper.ext_utils.menu_utils import Menus, rcloneListButtonMaker, rcloneListNextPage
from bot.helper.ext_utils.message_utils import editMessage, sendMessage
from bot.helper.ext_utils.button_build import ButtonMaker
from bot.helper.ext_utils.rclone_utils import create_next_buttons, is_rclone_config, is_valid_path, list_folder, list_remotes
from bot.helper.ext_utils.rclone_data_holder import get_rclone_data, update_rclone_data
from pyrogram.filters import regex
from pyrogram import filters
from pyrogram.handlers import CallbackQueryHandler, MessageHandler




async def handle_cloudselect(client, message):
    user_id= message.from_user.id
    if await is_rclone_config(user_id, message):
        if DEFAULT_OWNER_REMOTE := config_dict['DEFAULT_OWNER_REMOTE']:
            if user_id == OWNER_ID:
                update_rclone_data("CLOUD_SELECT_REMOTE", DEFAULT_OWNER_REMOTE, user_id)
        if config_dict['MULTI_RCLONE_CONFIG'] or CustomFilters._owner_query(user_id): 
            await list_remotes(message, menu_type='cloudselectmenu') 
        else:
            await sendMessage("Not allowed to use", message)        

async def cloudselect_callback(client, callback_query):
    query= callback_query
    data = query.data
    cmd = data.split("^")
    message = query.message
    user_id= query.from_user.id
    base_dir= get_rclone_data("CLOUD_SELECT_BASE_DIR", user_id)
    rclone_remote = get_rclone_data("CLOUD_SELECT_REMOTE", user_id)

    if int(cmd[-1]) != user_id:
        await query.answer("This menu is not for you!", show_alert=True)
        return
    if cmd[1] == "remote":
        if config_dict['MULTI_REMOTE_UP'] and user_id== OWNER_ID:
            remotes_multi.append(cmd[2])
            await list_remotes(message, menu_type='cloudselectmenu', edit=True)
            return
        update_rclone_data("CLOUD_SELECT_BASE_DIR", "", user_id) #Reset Dir
        update_rclone_data("CLOUD_SELECT_REMOTE", cmd[2], user_id)
        if user_id == OWNER_ID:
            config_dict.update({'DEFAULT_OWNER_REMOTE': cmd[2]}) 
        await list_folder(message, cmd[2], "", menu_type=Menus.CLOUDSELECT, edit=True)
    elif cmd[1] == "remote_dir":
        path = get_rclone_data(cmd[2], user_id)
        base_dir += path + "/"
        if await is_valid_path(rclone_remote, base_dir, message):
            update_rclone_data("CLOUD_SELECT_BASE_DIR", base_dir, user_id)
            await list_folder(message, rclone_remote, base_dir, menu_type=Menus.CLOUDSELECT, edit=True)
    elif cmd[1] == "back":
        if len(base_dir) == 0: 
            await list_remotes(message, menu_type='cloudselectmenu', edit=True)
            return 
        base_dir_split= base_dir.split("/")[:-2]
        base_dir_string = "" 
        for dir in base_dir_split: 
            base_dir_string += dir + "/"
        base_dir = base_dir_string
        update_rclone_data("CLOUD_SELECT_BASE_DIR", base_dir, user_id)
        await list_folder(message, rclone_remote, base_dir, menu_type=Menus.CLOUDSELECT, edit=True)
        await query.answer() 
    elif cmd[1] == "pages":
        await query.answer()
    elif cmd[1] == "reset":
        remotes_multi.clear()
        await list_remotes(message, menu_type='cloudselectmenu', edit=True)
    else:
        await query.answer()
        await message.delete()

async def next_page_cloudselect(client, callback_query):
    query= callback_query
    data= query.data
    message= query.message
    await query.answer()
    user_id= message.reply_to_message.from_user.id
    _, next_offset, _, data_back_cb = data.split()
    list_info = get_rclone_data("list_info", user_id)
    total = len(list_info)
    next_offset = int(next_offset)
    prev_offset = next_offset - 10 

    buttons = ButtonMaker()
    buttons.cb_buildbutton("✅ Select this folder", f"cloudselectmenu^close^{user_id}")

    next_list_info, _next_offset= rcloneListNextPage(list_info, next_offset) 
    
    rcloneListButtonMaker(result_list= next_list_info, 
        buttons= buttons,
        menu_type= Menus.CLOUDSELECT,
        dir_callback = "remote_dir",
        file_callback= "",
        user_id= user_id)
    
    await create_next_buttons(next_offset, 
        prev_offset, 
        _next_offset, 
        data_back_cb, 
        total, 
        user_id, 
        buttons, 
        filter= 'next_cloudselect',
        menu_type='cloudselectmenu')

    cloudselect_remote= get_rclone_data("CLOUD_SELECT_REMOTE", user_id)
    base_dir= get_rclone_data("CLOUD_SELECT_BASE_DIR", user_id)
    msg= f"Select folder where you want to store files\n\n<b>Path:</b><code>{cloudselect_remote}:{base_dir}</code>"
    await editMessage(msg, message, reply_markup= buttons.build_menu(1))
 
 
cloudselect_handler = MessageHandler(handle_cloudselect, filters= filters.command(BotCommands.CloudSelectCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter))
next_cloudselect_cb= CallbackQueryHandler(next_page_cloudselect, filters= regex("next_cloudselect"))
cloudselect_cb = CallbackQueryHandler(cloudselect_callback, filters= regex("cloudselectmenu"))

bot.add_handler(cloudselect_cb)
bot.add_handler(next_cloudselect_cb)
bot.add_handler(cloudselect_handler)