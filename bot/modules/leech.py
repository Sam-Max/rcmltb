from asyncio import TimeoutError
from json import loads as jsonloads
from os import path as ospath
from configparser import ConfigParser
from asyncio.subprocess import PIPE, create_subprocess_exec as exec
from pyrogram.filters import regex, command
from pyrogram.handlers import CallbackQueryHandler, MessageHandler
from pyrogram import filters
from bot import DOWNLOAD_DIR, bot, config_dict
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.filters import CustomFilters
from bot.helper.ext_utils.menu_utils import Menus, rcloneListButtonMaker, rcloneListNextPage
from bot.helper.ext_utils.message_utils import deleteMessage, editMessage, sendMarkup, sendMessage
from bot.helper.ext_utils.button_build import ButtonMaker
from bot.helper.ext_utils.rclone_utils import get_rclone_config, is_rclone_config
from bot.helper.ext_utils.rclone_data_holder import get_rclone_data, update_rclone_data
from bot.helper.mirror_leech_utils.download_utils.rclone_download import RcloneLeech
from bot.modules.listener import MirrorLeechListener
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
                msg= "<b>Multi zip by replying to first file:</b>"
                msg+= "\n\n<code>/cmd</code> 5 (number of files)"
                msg+= "\nNumber should be always before | zipname"
                await sendMessage(msg, message)
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
        return await query.answer("This menu is not for you!", show_alert=True)
    elif cmd[1] == "remote":
        #Reset menu
        update_rclone_data("LEECH_BASE_DIR", "", user_id)
        base_dir= get_rclone_data("LEECH_BASE_DIR", user_id)
        remote_name= cmd[2]
        update_rclone_data("LEECH_REMOTE", remote_name, user_id)
        await list_folder(message, remote_name= remote_name, remote_base=base_dir, edit=True)
        await query.answer()   
    elif cmd[1] == "remote_dir":
        path = get_rclone_data(cmd[2], user_id)
        base_dir += path + "/"
        update_rclone_data("LEECH_BASE_DIR", base_dir, user_id)
        await list_folder(message, remote_name= rclone_remote, remote_base=base_dir, edit=True)
        await query.answer()   
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
            await query.answer() 
            await list_remotes(message, edit=True)
            return 
        base_dir_split= base_dir.split("/")[:-2]
        base_dir_string = "" 
        for dir in base_dir_split: 
            base_dir_string += dir + "/"
        base_dir = base_dir_string
        update_rclone_data("LEECH_BASE_DIR", base_dir, user_id)
        await list_folder(message, remote_name= rclone_remote, remote_base=base_dir, edit=True)
        await query.answer()
    elif cmd[1] == "pages":
        await query.answer()
    else:
        await query.answer()
        await message.delete()

async def list_remotes(message, edit=False):
    if message.reply_to_message:
        user_id= message.reply_to_message.from_user.id
    else:
        user_id= message.from_user.id
    path= get_rclone_config(user_id)
    if not path:
        await sendMessage("Send a rclone config file, use /botfiles command", message)
        return
    conf = ConfigParser()
    conf.read(path)
    buttons = ButtonMaker()
    for remote in conf.sections():
        buttons.cb_buildbutton(f"📁 {remote}", f"leechmenu^remote^{remote}^{user_id}") 
    buttons.cb_buildbutton("✘ Close Menu", f"leechmenu^close^{user_id}")
    if edit:
        await editMessage("Select cloud where your files are stored\n\n<b>", message, reply_markup= buttons.build_menu(2))
    else:
        await sendMarkup("Select cloud where your files are stored\n\n<b>", message, reply_markup= buttons.build_menu(2))

async def list_folder(message, remote_name, remote_base, back= "back", edit=False):
    user_id= message.reply_to_message.from_user.id
    msg_id= message.reply_to_message.id
    info= listener_dict[msg_id] 
    is_zip= info[1]
    extract= info[2]
    buttons = ButtonMaker()
    path = get_rclone_config(user_id)
    buttons.cb_buildbutton("✅ Select this folder", f"leechmenu^leech_folder^{user_id}")

    cmd = ["rclone", "lsjson", f'--config={path}', f"{remote_name}:{remote_base}" ] 
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
        buttons.cb_buildbutton("❌Nothing to show❌", f"leechmenu^pages^{user_id}")
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
            dir_callback = "remote_dir",
            file_callback= 'leech_file',
            user_id= user_id)

        if offset == 0 and total <= 10:
            buttons.cb_buildbutton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", f"leechmenu^pages^{user_id}", 'footer')        
        else: 
            buttons.cb_buildbutton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", f"leechmenu^pages^{user_id}", 'footer')
            buttons.cb_buildbutton("NEXT ⏩", f"next_leech {next_offset} {back}", 'footer')

    buttons.cb_buildbutton("⬅️ Back", f"leechmenu^{back}^{user_id}", 'footer_second')
    buttons.cb_buildbutton("✘ Close Menu", f"leechmenu^close^{user_id}", 'footer_second')

    msg = f'Select folder or file that you want to leech\n\n<b>Path:</b><code>{remote_name}:{remote_base}</code>'
    if is_zip:
        msg = f'Select file that you want to zip\n\n<b>Path:</b><code>{remote_name}:{remote_base}</code>' 
    if extract:
        msg = f'Select file that you want to extract\n\n<b>Path:</b><code>{remote_name}:{remote_base}</code>'

    if edit:
        await editMessage(msg, message, reply_markup= buttons.build_menu(1))
    else:
        await sendMarkup(msg, message, reply_markup= buttons.build_menu(1))
 
async def next_page_leech(client, callback_query):
    query= callback_query
    data = query.data
    message= query.message
    await query.answer()
    user_id= message.reply_to_message.from_user.id
    _, next_offset, data_back_cb= data.split()
    list_info = get_rclone_data("list_info", user_id)
    total = len(list_info)
    next_offset = int(next_offset)
    prev_offset = next_offset - 10 

    buttons = ButtonMaker()
    buttons.cb_buildbutton(f"✅ Select this folder", f"leechmenu^leech_folder^{user_id}")

    next_list_info, _next_offset= rcloneListNextPage(list_info, next_offset)

    rcloneListButtonMaker(result_list= next_list_info,
        buttons=buttons,
        menu_type= Menus.LEECH, 
        dir_callback = "remote_dir",
        file_callback= 'leech_file',
        user_id= user_id)

    if next_offset == 0:
        buttons.cb_buildbutton(f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", "leechmenu^pages", 'footer')
        buttons.cb_buildbutton("NEXT ⏩", f"next_leech {_next_offset} {data_back_cb}", 'footer')
    
    elif next_offset >= total:
        buttons.cb_buildbutton("⏪ BACK", f"next_leech {prev_offset} {data_back_cb}", 'footer') 
        buttons.cb_buildbutton(f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", "leechmenu^pages", 'footer')
   
    elif next_offset + 10 > total:
        buttons.cb_buildbutton("⏪ BACK", f"next_leech {prev_offset} {data_back_cb}", 'footer')
        buttons.cb_buildbutton(f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", "leechmenu^pages", 'footer')
    else:
        buttons.cb_buildbutton("⏪ BACK", f"next_leech {prev_offset} {data_back_cb}", 'footer_second')
        buttons.cb_buildbutton(f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", "leechmenu^pages", 'footer')
        buttons.cb_buildbutton("NEXT ⏩", f"next_leech {_next_offset} {data_back_cb}", 'footer_second')

    buttons.cb_buildbutton("⬅️ Back", f"leechmenu^{data_back_cb}^{user_id}", 'footer_third')
    buttons.cb_buildbutton("✘ Close Menu", f"leechmenu^close^{user_id}", 'footer_third')

    leech_remote= get_rclone_data("LEECH_REMOTE", user_id)
    base_dir= get_rclone_data("LEECH_BASE_DIR", user_id)
    await editMessage(f"Select folder or file that you want to leech\n\n<b>Path:</b><code>{leech_remote}:{base_dir}</code>", message, 
                        reply_markup= buttons.build_menu(1))    
           
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
        return await query.answer("This menu is not for you!", show_alert=True)
    elif cmd[1] == "link":
        await query.answer()     
        question= await sendMessage("Send link to leech, /ignore to cancel", message)
        try:
            response = await client.listen.Message(filters.text, id=filters.user(user_id), timeout= 30)
        except TimeoutError:
            await sendMessage("Too late 30s gone, try again!", message)
        else:
            if response:
                try:
                    if "/ignore" in response.text:
                        await client.listen.Cancel(filters.user(user_id))
                    else:
                        message= listener.message
                        message.text = f"/leech {response.text}"
                        await mirror_leech(client, message, isZip=is_zip, extract=extract, isLeech=True)
                except Exception as ex:
                        await sendMessage(str(ex), message) 
        finally:
            await question.delete()
    elif cmd[1] == "remotes":
        await list_remotes(message, edit=True)
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