from configparser import ConfigParser
from json import loads as jsonloads
from re import escape as rescape
from os import getcwd, path as ospath
from asyncio import create_subprocess_exec
from asyncio.subprocess import PIPE
from bot import GLOBAL_EXTENSION_FILTER, LOGGER, OWNER_ID, config_dict, remotes_multi
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.ext_utils.exceptions import NotRclonePathFound
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.ext_utils.menu_utils import Menus, rcloneListButtonMaker
from bot.helper.telegram_helper.message_utils import editMessage, sendMarkup, sendMessage
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.rclone_data_holder import get_rclone_data, update_rclone_data
from configparser import ConfigParser            
            


async def is_remote_selected(user_id, message):
    if config_dict['MULTI_RCLONE_CONFIG'] or CustomFilters._owner_query(user_id):
        if DEFAULT_OWNER_REMOTE:= config_dict['DEFAULT_OWNER_REMOTE']:
            update_rclone_data("MIRROR_SELECT_REMOTE", DEFAULT_OWNER_REMOTE, user_id)
            return True
        elif get_rclone_data("MIRROR_SELECT_REMOTE", user_id) or len(remotes_multi) > 0:
            return True
        else:
            await sendMessage(f"Select a cloud first, use /{BotCommands.MirrorSelectCommand[0]}", message)
            return False
    else:
        return True

async def is_rclone_config(user_id, message, isLeech=False):
    path = f'{getcwd()}/rclone/'
    if config_dict['MULTI_RCLONE_CONFIG'] or CustomFilters._owner_query(user_id):
        path= ospath.join(path, f'{user_id}', "rclone.conf")
        msg= "Send a rclone config file, use /botfiles command"
    else:
        path= ospath.join(path, "rclone_global", "rclone.conf")
        msg= "Global rclone not found"
    if ospath.exists(path):
        return True
    else:
        if isLeech: 
            return True
        else:
            await sendMessage(msg, message)
            return False    

async def get_rclone_path(user_id, message= None):
    path = f'{getcwd()}/rclone/'
    if config_dict['MULTI_RCLONE_CONFIG'] or CustomFilters._owner_query(user_id):
        rc_path = ospath.join(path, f"{user_id}" , "rclone.conf")
    else:
        rc_path = ospath.join(path, "rclone_global", "rclone.conf")      
    if ospath.exists(rc_path): 
        return rc_path 
    else:
        await sendMessage("Rclone path not found", message)
        raise NotRclonePathFound(f"ERROR: Rclone path not found")

async def setRcloneFlags(cmd, type):
    ext = '*.{' + ','.join(GLOBAL_EXTENSION_FILTER) + '}'
    cmd.extend(('--exclude', ext))
    if type == "copy":
        if flags := config_dict.get('RCLONE_COPY_FLAGS'):
            append_flags(flags,cmd)
    elif type == "upload":
        if flags := config_dict.get('RCLONE_UPLOAD_FLAGS'):
            append_flags(flags,cmd)
    elif type == "download":
        if flags := config_dict.get('RCLONE_DOWNLOAD_FLAGS'):
            append_flags(flags,cmd)
           
def append_flags(flags, cmd):
    rcflags = flags.split(',')
    for flag in rcflags:
        if ":" in flag:
            key, value = flag.split(":")
            cmd.extend((key, value))
        elif len(flag) > 0:
            cmd.append(flag)

async def list_remotes(message, menu_type, remote_type='remote', is_second_menu=False, edit=False):
    if message.reply_to_message:
        user_id= message.reply_to_message.from_user.id
    else:
        user_id= message.from_user.id
    path= await get_rclone_path(user_id, message)
    conf = ConfigParser()
    conf.read(path)
    buttons = ButtonMaker()
    for remote in conf.sections():
        prev = ""
        if config_dict['MULTI_REMOTE_UP'] and user_id== OWNER_ID:
            if remote in remotes_multi: prev = "✅"
            buttons.cb_buildbutton(f"{prev} 📁 {remote}", f"{menu_type}^{remote_type}^{remote}^{user_id}")
        else:
            buttons.cb_buildbutton(f"📁 {remote}", f"{menu_type}^{remote_type}^{remote}^{user_id}")
    if menu_type== Menus.REMOTE_SELECT:
        msg= f"Select cloud where you want to mirror the file"
    if menu_type == Menus.CLEANUP:
        msg= "Select cloud to delete trash"
    elif menu_type == Menus.STORAGE:
        msg= "Select cloud to view info"
    elif menu_type == Menus.MIRROR_SELECT:
        if config_dict['MULTI_REMOTE_UP']:
            msg= f"Select all clouds where you want to upload file"
            buttons.cb_buildbutton("🔄 Reset", f"{menu_type}^reset^{user_id}", 'footer')  
        else:
            remote= get_rclone_data("MIRROR_SELECT_REMOTE", user_id)
            dir= get_rclone_data("MIRROR_SELECT_BASE_DIR", user_id)
            msg= f"Select cloud where you want to store files\n\n<b>Path:</b><code>{remote}:{dir}</code>"  
    elif menu_type == Menus.SYNC:
        msg= f"Select <b>{remote_type}</b> cloud"
        msg+= "<b>\n\nNote</b>: Sync make source and destination identical, modifying destination only."
    else:
        msg= "Select cloud where your files are stored\n\n"     
    if is_second_menu:
        msg = 'Select folder where you want to copy' 
    buttons.cb_buildbutton("✘ Close Menu", f"{menu_type}^close^{user_id}", 'footer')
    if edit:
        await editMessage(msg, message, reply_markup= buttons.build_menu(2))
    else:
        await sendMarkup(msg, message, reply_markup= buttons.build_menu(2))

async def create_next_buttons(next_offset, prev_offset, _next_offset, data_back_cb, total, user_id, buttons, filter, menu_type, is_second_menu=False):
    if next_offset == 0:
        buttons.cb_buildbutton(f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", f"{menu_type}^pages", 'footer')
        buttons.cb_buildbutton("NEXT ⏩", f"{filter} {_next_offset} {is_second_menu} {data_back_cb}", 'footer')
    elif next_offset >= total:
        buttons.cb_buildbutton("⏪ BACK", f"{filter} {prev_offset} {is_second_menu} {data_back_cb}", 'footer') 
        buttons.cb_buildbutton(f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", f"{menu_type}^pages", 'footer')
    elif next_offset + 10 > total:
        buttons.cb_buildbutton("⏪ BACK", f"{filter} {prev_offset} {is_second_menu} {data_back_cb}", 'footer')
        buttons.cb_buildbutton(f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", f"{menu_type}^pages", 'footer')
    else:
        buttons.cb_buildbutton("⏪ BACK", f"{filter} {prev_offset} {is_second_menu} {data_back_cb}", 'footer_second')
        buttons.cb_buildbutton(f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", f"{menu_type}^pages", 'footer')
        buttons.cb_buildbutton("NEXT ⏩", f"{filter} {_next_offset} {is_second_menu} {data_back_cb}", 'footer_second')
    buttons.cb_buildbutton("⬅️ Back", f"{menu_type}^{data_back_cb}^{user_id}", 'footer_third')
    buttons.cb_buildbutton("✘ Close Menu", f"{menu_type}^close^{user_id}", 'footer_third')

async def is_valid_path(remote, path, message):
    user_id= message.reply_to_message.from_user.id
    rc_path = await get_rclone_path(user_id, message)
    cmd = ["rclone", "lsjson", f'--config={rc_path}', f"{remote}:{path}"]
    process = await create_subprocess_exec(*cmd, stdout=PIPE)
    return_code = await process.wait()
    if return_code != 0:
        LOGGER.info('Error: Path not valid')
        return False
    else:
        return True

async def list_folder(message, rclone_remote, base_dir, menu_type, listener_dict={}, is_second_menu=False, edit=False):
    user_id= message.reply_to_message.from_user.id
    buttons = ButtonMaker()
    path = await get_rclone_path(user_id, message)
    dir_callback = "remote_dir"
    back_callback= "back"
    cmd = ["rclone", "lsjson", f'--config={path}', f"{rclone_remote}:{base_dir}"]
    
    if menu_type == Menus.LEECH:
        next_type= "next_leech" 
        file_callback= 'leech_file'
        try:
            info = listener_dict[message.reply_to_message.id]
            is_zip, extract = info[1], info[2]
            cmd.extend(['--fast-list', '--no-modtime'])
            buttons.cb_buildbutton("✅ Select this folder", f"{menu_type}^leech_folder^{user_id}")
            if is_zip:
                msg = f'Select file that you want to zip\n\n<b>Path:</b><code>{rclone_remote}:{base_dir}</code>' 
            elif extract:
                msg = f'Select file that you want to extract\n\n<b>Path:</b><code>{rclone_remote}:{base_dir}</code>'
            else:
                msg = f'Select folder or file that you want to leech\n\n<b>Path:</b><code>{rclone_remote}:{base_dir}</code>'
        except KeyError:
             LOGGER.info("Key not found in listener_dict")
             raise ValueError("Invalid key") 
    elif menu_type == Menus.MIRROR_SELECT:
        next_type= "next_ms"
        file_callback= ""
        cmd.extend(['--dirs-only', '--fast-list', '--no-modtime'])
        buttons.cb_buildbutton("✅ Select this folder", f"{menu_type}^close^{user_id}")
        msg= f"Select folder where you want to store files\n\n<b>Path:</b><code>{rclone_remote}:{base_dir}</code>"
    elif menu_type == Menus.MYFILES:
        next_type= 'next_myfiles'
        file_callback= "file_action"
        cmd.extend(['--fast-list', '--no-modtime'])
        buttons.cb_buildbutton(f"⚙️ Folder Options", f"{menu_type}^folder_action^{user_id}")
        buttons.cb_buildbutton("🔍 Search", f"myfilesmenu^search^{user_id}")
        msg= f"Your cloud files are listed below\n\n<b>Path:</b><code>{rclone_remote}:{base_dir}</code>"
    elif menu_type == Menus.COPY:
        next_type= 'next_copy'
        if is_second_menu:
            file_callback = 'copy'
            dir_callback="dest_dir" 
            back_callback= "back_dest"
            buttons.cb_buildbutton(f"✅ Select this folder", f"{menu_type}^copy^{user_id}")
            cmd.extend(['--dirs-only', '--fast-list', '--no-modtime']) 
            msg=f'Select folder where you want to copy\n\n<b>Path: </b><code>{rclone_remote}:{base_dir}</code>'
        else:
            file_callback = 'second_menu'
            dir_callback="origin_dir"
            back_callback= "back_origin"
            buttons.cb_buildbutton(f"✅ Select this folder", f"{menu_type}^second_menu^_^False^{user_id}")
            cmd.extend(['--fast-list', '--no-modtime'])
            msg= f'Select file or folder which you want to copy\n\n<b>Path: </b><code>{rclone_remote}:{base_dir}</code>'
    else:
        await sendMessage("Invalid menu type specified!", message)
        return

    process = await create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
    out, err = await process.communicate()
    out = out.decode().strip()
    return_code = await process.wait()
    if return_code != 0:
        err = err.decode().strip()
        await sendMessage(f'Error: {err}', message)
        return

    info = jsonloads(out)
    if is_second_menu:
        info_sorted= sorted(info, key=lambda x: x["Name"])
    else:
        info_sorted= sorted(info, key=lambda x: x["Size"])
    
    update_rclone_data("list_info", info_sorted, user_id)
    
    if len(info_sorted) == 0:
        buttons.cb_buildbutton("❌Nothing to show❌", f"{menu_type}^pages^{user_id}")
    else:
        total = len(info_sorted)
        max_results= 10
        offset= 0
        start = offset
        end = max_results + start
        next_offset = offset + max_results

        if end > total:
            info= info_sorted[offset:]    
        elif offset >= total:
            info= []    
        else:
            info= info_sorted[start:end]       
        
        rcloneListButtonMaker(info= info,
            buttons=buttons,
            menu_type= menu_type, 
            dir_callback = dir_callback,
            file_callback= file_callback,
            user_id= user_id)

        if offset == 0 and total <= 10:
            buttons.cb_buildbutton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", f"{menu_type}^pages^{user_id}", 'footer')        
        else: 
            buttons.cb_buildbutton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", f"{menu_type}^pages^{user_id}", 'footer')
            buttons.cb_buildbutton("NEXT ⏩", f"{next_type} {next_offset} {is_second_menu} {back_callback}", 'footer')

    buttons.cb_buildbutton("⬅️ Back", f"{menu_type}^{back_callback}^{user_id}", 'footer_second')
    buttons.cb_buildbutton("✘ Close Menu", f"{menu_type}^close^{user_id}", 'footer_third')

    if edit:
        await editMessage(msg, message, reply_markup= buttons.build_menu(1))
    else:
        await sendMarkup(msg, message, reply_markup= buttons.build_menu(1))


async def get_drive_link(remote, base, name, conf, mime_type, buttons):
    if mime_type == "Folder":
        s_name = rescape(name.replace(".", ""))
        cmd = ["rclone", "lsjson", f'--config={conf}', f"{remote}:{base}", "--dirs-only", "-f", f"+ {s_name}/", "-f", "- *"]
    else:
        s_name = rescape(name)
        cmd = ["rclone", "lsjson", f'--config={conf}', f"{remote}:{base}", "--files-only", "-f", f"+ {s_name}", "-f", "- *"]
    process = await create_subprocess_exec(*cmd,stdout= PIPE,stderr= PIPE)
    stdout, stderr = await process.communicate()
    return_code = await process.wait()
    stdout = stdout.decode().strip()
    if return_code != 0:
        LOGGER.error(f'Error: {stderr.decode().strip()}') 
        return
    data = jsonloads(stdout)
    if data:
        id = data[0]["ID"]
        if mime_type == "Folder":
            link = f'https://drive.google.com/drive/folders/{id}'
            buttons.url_buildbutton('Cloud Link 🔗', link)
        else:
            link = f'https://drive.google.com/uc?id={id}&export=download'
            buttons.url_buildbutton('Cloud Link 🔗', link)
    else:
        LOGGER.error("Error while getting id")
        link = 'https://drive.google.com/file/d/err/view'
        buttons.url_buildbutton("🚫", link)
        