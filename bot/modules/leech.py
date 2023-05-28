from asyncio import TimeoutError
from os import path as ospath
from pyrogram.filters import regex, command
from pyrogram.handlers import CallbackQueryHandler, MessageHandler
from pyrogram import filters
from bot import DOWNLOAD_DIR, bot, config_dict
from bot.helper.ext_utils.help_messages import MULTIZIP_HELP_MESSAGE
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.ext_utils.menu_utils import Menus, rcloneListButtonMaker, rcloneListNextPage
from bot.helper.telegram_helper.message_utils import deleteMessage, editMessage, sendMarkup, sendMessage
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.rclone_utils import create_next_buttons, is_rclone_config, is_valid_path, list_folder, list_remotes
from bot.helper.ext_utils.rclone_data_holder import get_rclone_data, update_rclone_data
from bot.helper.mirror_leech_utils.download_utils.rclone_download import RcloneLeech
from bot.modules.tasks_listener import MirrorLeechListener
from bot.modules.mirror_leech import mirror_leech


listener_dict = {}



async def handle_zip_leech_command(client, message):
    await leech(client, message, isZip=True)

async def handle_unzip_leech_command(client, message):
    await leech(client, message, extract=True)

async def handle_multizip_leech(client, message):
    await leech(client, message, multiZip=True)       

async def handle_leech(client, message):
     await leech(client, message)

async def leech(client, message, extract=False, isZip=False, multiZip=False):
    user_id= message.from_user.id
    tag = f"@{message.from_user.username}"
    if await is_rclone_config(user_id, message, isLeech=True):
        listener= MirrorLeechListener(message, tag, user_id, isZip=isZip, extract=extract, isLeech=True)
        listener_dict[message.id] = [listener, isZip, extract]
        buttons= ButtonMaker()
        buttons.cb_buildbutton("🔗 From Link", f"leechselect^link^{user_id}")
        buttons.cb_buildbutton("📁 From Cloud", f"leechselect^remotes^{user_id}")
        buttons.cb_buildbutton("✘ Close Menu", f"leechselect^close^{user_id}")    
        if multiZip:
            if message.reply_to_message:
                await mirror_leech(client, message, isZip=isZip, extract=extract, isLeech=True, multiZip=multiZip)
            else:
                await sendMessage(MULTIZIP_HELP_MESSAGE, message)
            return
        if config_dict['MULTI_RCLONE_CONFIG'] or CustomFilters._owner_query(user_id): 
            if message.reply_to_message:
                await mirror_leech(client, message, isZip=isZip, extract=extract, isLeech=True, multiZip=multiZip)
            else:
                await sendMarkup("Select from where you want to leech", message, buttons.build_menu(2))  
        else:
            if message.reply_to_message:
                await mirror_leech(client, message, isZip=isZip, extract=extract, isLeech=True, multiZip=multiZip)
            else:
                await sendMessage("Reply to a link/file", message)

async def leech_menu_cb(client, callback_query):
    query= callback_query
    data = query.data
    cmd = data.split("^")
    message = query.message
    user_id= query.from_user.id
    msg_id= message.reply_to_message.id
    info= listener_dict[msg_id] 
    listener= info[0]
    base_dir= get_rclone_data("LEECH_BASE_DIR", user_id)
    rclone_remote = get_rclone_data("LEECH_REMOTE", user_id)

    if int(cmd[-1]) != user_id:
         await query.answer("This menu is not for you!", show_alert=True)
         return
    elif cmd[1] == "remote":
        update_rclone_data("LEECH_BASE_DIR", "", user_id) # Reset Dir
        update_rclone_data("LEECH_REMOTE", cmd[2], user_id)
        await list_folder(message, cmd[2], "", menu_type=Menus.LEECH, listener_dict= listener_dict, edit=True)
    elif cmd[1] == "remote_dir":
        path = get_rclone_data(cmd[2], user_id)
        base_dir += path + "/"
        if await is_valid_path(rclone_remote, base_dir, message):
            update_rclone_data("LEECH_BASE_DIR", base_dir, user_id)
            await list_folder(message, rclone_remote, base_dir, menu_type=Menus.LEECH, listener_dict= listener_dict, edit=True)
    elif cmd[1] == "leech_file":
        await query.answer()      
        path = get_rclone_data(cmd[2], user_id)
        base_dir += path
        name, _ = ospath.splitext(base_dir)
        dest_dir = f'{DOWNLOAD_DIR}{msg_id}/{name}'
        await deleteMessage(message)
        await RcloneLeech(base_dir, dest_dir, listener).leech()
    elif cmd[1] == "leech_folder":
        await query.answer() 
        dest_dir = f'{DOWNLOAD_DIR}{msg_id}/{base_dir}'
        await deleteMessage(message)
        await RcloneLeech(base_dir, dest_dir, listener, isFolder=True).leech()
    elif cmd[1] == "back":
        if len(base_dir) == 0:
            await list_remotes(message, menu_type='leechmenu', edit=True)
            return 
        base_dir_split= base_dir.split("/")[:-2]
        base_dir_string = "" 
        for dir in base_dir_split: 
            base_dir_string += dir + "/"
        base_dir = base_dir_string
        update_rclone_data("LEECH_BASE_DIR", base_dir, user_id)
        await list_folder(message, rclone_remote, base_dir, menu_type=Menus.LEECH, listener_dict= listener_dict, edit=True)
    elif cmd[1] == "pages":
        await query.answer()
    else:
        await message.delete()

async def next_page_leech(client, callback_query):
    query= callback_query
    data = query.data
    message= query.message
    await query.answer()
    user_id= message.reply_to_message.from_user.id
    _, next_offset, _, data_back_cb= data.split()
    list_info = get_rclone_data("list_info", user_id)
    total = len(list_info)
    next_offset = int(next_offset)
    prev_offset = next_offset - 10 

    buttons = ButtonMaker()
    buttons.cb_buildbutton(f"✅ Select this folder", f"leechmenu^leech_folder^{user_id}")

    next_list_info, _next_offset= rcloneListNextPage(list_info, next_offset)

    rcloneListButtonMaker(info= next_list_info,
        buttons=buttons,
        menu_type= Menus.LEECH, 
        dir_callback = "remote_dir",
        file_callback= 'leech_file',
        user_id= user_id)
    
    await create_next_buttons(next_offset, 
        prev_offset, 
        _next_offset, 
        data_back_cb, 
        total, 
        user_id, 
        buttons, 
        filter= 'next_leech',
        menu_type=Menus.LEECH)

    leech_remote= get_rclone_data("LEECH_REMOTE", user_id)
    base_dir= get_rclone_data("LEECH_BASE_DIR", user_id)
    msg= f"Select folder or file that you want to leech\n\n<b>Path:</b><code>{leech_remote}:{base_dir}</code>"
    await editMessage(msg, message, reply_markup= buttons.build_menu(1))    
           
async def selection_callback(client, callback_query):
    query= callback_query
    data = query.data
    cmd = data.split("^")
    message = query.message
    msg_id= message.reply_to_message.id
    info= listener_dict[msg_id] 
    listener= info[0]
    is_zip= info[1]
    extract= info[2]
    user_id= query.from_user.id

    if int(cmd[-1]) != user_id:
        await query.answer("This menu is not for you!", show_alert=True)
        return
    elif cmd[1] == "link":
        await query.answer()     
        question= await sendMessage("Send link to leech, /ignore to cancel", message)
        try:
            response = await client.listen.Message(filters.text, id=filters.user(user_id), timeout= 30)
            if response:
                if "/ignore" in response.text:
                    await client.listen.Cancel(filters.user(user_id))
                else:
                    message= listener.message
                    message.text = f"/leech {response.text}"
                    await mirror_leech(client, message, isZip=is_zip, extract=extract, isLeech=True)
        except TimeoutError:
            await sendMessage("Too late 30s gone, try again!", message)
        finally:
            await question.delete()
    elif cmd[1] == "remotes":
        if await is_rclone_config(user_id, message):
            await list_remotes(message, menu_type='leechmenu', edit=True)
            await query.answer()
    else:
        await query.answer()
        await message.delete()


leech_handler = MessageHandler(handle_leech, filters= command(BotCommands.LeechCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter))
zip_leech_handler = MessageHandler(handle_zip_leech_command, filters= command(BotCommands.ZipLeechCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter))
unzip_leech_handler = MessageHandler(handle_unzip_leech_command, filters= command(BotCommands.UnzipLeechCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter))
multizip_leech_handler = MessageHandler(handle_multizip_leech, filters=filters.command(BotCommands.MultiZipLeechCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter))
next_page_cb= CallbackQueryHandler(next_page_leech, filters= regex("next_leech"))
leech_callback= CallbackQueryHandler(leech_menu_cb, filters= regex("leechmenu"))
selection_cb= CallbackQueryHandler(selection_callback, filters= regex("leechselect"))

bot.add_handler(next_page_cb)
bot.add_handler(leech_callback)
bot.add_handler(selection_cb)
bot.add_handler(leech_handler)
bot.add_handler(zip_leech_handler)
bot.add_handler(unzip_leech_handler)
bot.add_handler(multizip_leech_handler)