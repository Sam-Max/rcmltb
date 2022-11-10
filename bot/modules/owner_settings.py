# Source: https://github.com/anasty17/mirror-leech-telegram-bot/blob/master/bot/modules/bot_settings.py
# Some minor modifications from source

from asyncio import TimeoutError
from os import environ
from subprocess import Popen, run as srun
from pyrogram.filters import regex, command
from pyrogram import filters
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from bot import ALLOWED_CHATS, GLOBAL_EXTENSION_FILTER, SUDO_USERS, TG_MAX_FILE_SIZE, bot, Interval, aria2, config_dict, aria2_options, aria2c_global, get_client, qbit_options, status_reply_dict_lock
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.bot_utils import setInterval 
from bot.helper.ext_utils.db_handler import DbManger
from bot.helper.ext_utils.filters import CustomFilters
from bot.helper.ext_utils.message_utils import editMarkup, sendFile, sendMarkup, update_all_messages
from bot.helper.ext_utils.misc_utils import ButtonMaker
from bot.helper.ext_utils.var_holder import update_rclone_var
from bot.modules.search import initiate_search_tools


START = 0
STATE = 'view'

default_values = {'AUTO_DELETE_MESSAGE_DURATION': 30,
                  'UPSTREAM_BRANCH': 'master',
                  'STATUS_UPDATE_INTERVAL': 10,
                  'LEECH_SPLIT_SIZE': TG_MAX_FILE_SIZE,
                  'SEARCH_LIMIT': 0,
                  'SERVER_PORT': 80,
                  'RSS_DELAY': 900}

async def handle_ownerset(client, message):
    text, buttons= get_env_menu()
    await sendMarkup(text, message, reply_markup= buttons.build_menu(2))  

async def edit_menus(message, edit_type="env"):
    if edit_type == "env":
        text, buttons= get_env_menu()   
        await editMarkup(text, message, reply_markup= buttons.build_menu(2))
    elif edit_type == "aria":
        text, buttons= get_aria_menu()   
        await editMarkup(text, message, reply_markup= buttons.build_menu(2))
    elif edit_type == "qbit":
        text, buttons= get_qbit_menu()   
        await editMarkup(text, message, reply_markup= buttons.build_menu(2))

def get_env_menu():
    msg= f"❇️<b>Config Variables Settings</b>"
    msg += f"\n\n<b>State: {STATE.upper()} </b>"
    msg += "\n\n<b>Notes:</b>"
    msg += "\n1. Use database for sudo and allowed users to persist when bot restarted"
    msg += "\n2. OWNER_ID, BOT_TOKEN, DOWNLOAD_DIR and DATABASE_URL, are non-editable while bot is running"
    msg += "\n3. Aria and qbit settings won't be saved after restart (no db support yet)"
    buttons= ButtonMaker() 
    for k in list(config_dict.keys())[START: 10 + START]:
        buttons.cb_buildbutton(k, f"ownersetmenu^env^editenv^{k}")
    if STATE == 'view':
        buttons.cb_buildbutton('Edit', "ownersetmenu^edit^env")
    else:
        buttons.cb_buildbutton('View', "ownersetmenu^view^env")
    buttons.cb_buildbutton("Aria2 Settings", "ownersetmenu^aria^aria_menu")
    buttons.cb_buildbutton("Qbit Setttings", "ownersetmenu^qbit^qbit_menu")
    pages= 0
    for x in range(0, len(config_dict)-1, 10):
        pages = int(x/10)
    buttons.cb_buildbutton(f"🗓 {int(START/10)}/{pages}", "ownersetmenu^page")  
    buttons.cb_buildbutton('⏪ BACK', "ownersetmenu^env^back", "footer")
    buttons.cb_buildbutton("NEXT ⏩", f"ownersetmenu^env^next", "footer")
    buttons.cb_buildbutton("✘ Close Menu", "ownersetmenu^close", "footer_second") 
    return msg, buttons

def get_qbit_menu():
    msg= "❇️<b>Qbit Settings</b>"
    msg += f"\n\n<b>State: {STATE.upper()} </b>"
    buttons= ButtonMaker() 
    for k in list(qbit_options.keys())[START: 10 + START]:
        buttons.cb_buildbutton(k, f"ownersetmenu^qbit^editqbit^{k}")
    if STATE == 'view':
        buttons.cb_buildbutton('Edit', "ownersetmenu^edit^qbit")
    else:
        buttons.cb_buildbutton('View', "ownersetmenu^view^qbit")
    pages= 0
    for x in range(0, len(qbit_options)-1, 10):
        pages = int(x/10)
    buttons.cb_buildbutton(f"🗓 {int(START/10)}/{pages}", "ownersetmenu^page")
    buttons.cb_buildbutton('⬅️ Back', "ownersetmenu^back", "footer")  
    buttons.cb_buildbutton('⏪ BACK', "ownersetmenu^qbit^back", "footer")
    buttons.cb_buildbutton("NEXT ⏩", f"ownersetmenu^qbit^next", "footer")
    buttons.cb_buildbutton("✘ Close Menu", "ownersetmenu^close", "footer_second") 
    return msg, buttons

def get_aria_menu():
    msg= "❇️<b>Aria2 Settings</b>"
    msg += f"\n\n<b>State: {STATE.upper()} </b>"
    buttons= ButtonMaker() 
    for k in list(aria2_options.keys())[START: 10 + START]:
        buttons.cb_buildbutton(k, f"ownersetmenu^aria^editaria^{k}")
    if STATE == 'view':
        buttons.cb_buildbutton('Edit', "ownersetmenu^edit^aria")
    else:
        buttons.cb_buildbutton('View', "ownersetmenu^view^aria")
    buttons.cb_buildbutton('Add new key', "ownersetmenu^aria^editaria^newkey")
    pages= 0
    for x in range(0, len(aria2_options)-1, 10):
        pages = int(x/10)
    buttons.cb_buildbutton(f"🗓 {int(START/10)}/{pages}", "ownersetmenu^page") 
    buttons.cb_buildbutton('⬅️ Back', "ownersetmenu^back")  
    buttons.cb_buildbutton('⏪ BACK', "ownersetmenu^aria^back", "footer")
    buttons.cb_buildbutton("NEXT ⏩", f"ownersetmenu^aria^next", "footer")
    buttons.cb_buildbutton("✘ Close Menu", "ownersetmenu^close", "footer_second") 
    return msg, buttons

async def update_buttons(message, key, edit_type=None): 
    buttons = ButtonMaker()
    msg= ""
    if edit_type == 'editenv':  
        buttons.cb_buildbutton('Back', "ownersetmenu^back^env")
        if key not in ['TELEGRAM_HASH', 'TELEGRAM_API']:
            buttons.cb_buildbutton('Default', f"ownersetmenu^env^resetenv^{key}")
        buttons.cb_buildbutton('Close', "ownersetmenu^close")
        msg= "Send new value for selected variable, /ignore to cancel. Timeout: 60 sec"
    elif edit_type == 'editaria':
        buttons.cb_buildbutton('Back', "ownersetmenu^back^aria")
        if key != 'newkey':
            buttons.cb_buildbutton('Default', f"ownersetmenu^aria^resetaria^{key}")
        buttons.cb_buildbutton('Close', "ownersetmenu^close")
        if key == 'newkey':
            msg = f'Send a key with value. Example: https-proxy-user:value'
        else:
            msg = f'Send a valid value for {key}. Timeout: 60 sec'
    elif edit_type == 'editqbit':
        msg = f'Send a valid value for {key}. Timeout: 60 sec'
        buttons.cb_buildbutton('Back', "ownersetmenu^back^qbit")
        buttons.cb_buildbutton('Close', "ownersetmenu^close")
    await editMarkup(msg, message, reply_markup= buttons.build_menu(2))
            
async def ownerset_callback(client, callback_query):
    query= callback_query
    data = query.data
    cmd = data.split("^")
    message = query.message
    user_id= query.from_user.id

    if cmd[1] == "env":
        if cmd[2] == "next":
            await query.answer()
            globals()['START'] += 10
            if START > len(config_dict):
                globals()['START'] = START - 10
            await edit_menus(message, 'env')
        elif cmd[2] == "back":
            await query.answer()
            globals()['START'] -= 10
            if START < 0:
                globals()['START'] += 10
            await edit_menus(message, 'env')
        elif cmd[2] == "editenv" and STATE == 'edit':
            if cmd[3] in ['RSS_USER_SESSION_STRING', 'AUTO_MIRROR', 'CMD_INDEX', 'USER_SESSION_STRING', 
                            'TELEGRAM_API_HASH', 'TELEGRAM_API_ID', 'RSS_DELAY']:
                await query.answer(text='Restart required for this to apply!', show_alert=True)
            else:
                await query.answer()
            await update_buttons(message, cmd[3], cmd[2]) 
            await start_env_listener(client, query, user_id, cmd[3])
        elif cmd[2] == 'editenv' and STATE == 'view':
            value = config_dict[cmd[3]]
            if len(str(value)) > 200:
                await query.answer()
                filename = f"{data[2]}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f'{value}')
                await sendFile(message, filename)
                return
            if value == '':
                value = None
            await query.answer(text=f'{value}', show_alert=True)
        elif cmd[2] == "resetenv":
            value = ''
            if cmd[3] == "SUDO_USERS" or cmd[3] == "ALLOWED_CHATS":
                await start_env_listener(client, query, user_id, cmd[3], action="rem")
            elif cmd[3] in default_values:
                value = default_values[cmd[3]]
            elif cmd[3] == 'DEFAULT_REMOTE':
                update_rclone_var("MIRRORSET_DRIVE", value, user_id)
                update_rclone_var("MIRRORSET_BASE_DIR", value, user_id)
            elif cmd[3] == 'EXTENSION_FILTER':
                GLOBAL_EXTENSION_FILTER.clear()
                GLOBAL_EXTENSION_FILTER.append('.aria2')
            elif cmd[3] == 'TORRENT_TIMEOUT':
                aria2.set_global_options({'bt-stop-timeout': 0})
            elif cmd[3] == 'BASE_URL':
                srun(["pkill", "-9", "-f", "gunicorn"])
            elif cmd[3] == 'SERVER_PORT':
                srun(["pkill", "-9", "-f", "gunicorn"])
                Popen("gunicorn web.wserver:app --bind 0.0.0.0:80", shell=True)
            await query.answer(f"{cmd[3]} reseted")    
            config_dict[cmd[3]] = value
            environ[cmd[3]]= str(value)
            await edit_menus(message, 'env')
    elif cmd[1] == "aria":
        if cmd[2] == 'aria_menu':
            globals()['START'] = 0
            await edit_menus(message, "aria")
        if cmd[2] == "next":
            await query.answer()
            globals()['START'] += 10
            if START > len(aria2_options):
                globals()['START'] = START - 10
            await edit_menus(message, "aria")
        elif cmd[2] == "back":
            await query.answer()
            globals()['START'] -= 10
            if START < 0:
                globals()['START'] += 10
            await edit_menus(message, "aria")
        elif cmd[2] == 'resetaria':
            aria2_defaults = aria2.client.get_global_option()
            if aria2_defaults[cmd[3]] == aria2_options[cmd[3]]:
                await query.answer(text='Value already same as you added in aria.sh!', show_alert= True)
                return
            await query.answer()
            value = aria2_defaults[cmd[3]]
            aria2_options[cmd[3]] = value
            await edit_menus(message, "aria")
        elif cmd[2] == "editaria" and (STATE == 'edit' or cmd[3] == 'newkey'):
            await update_buttons(message, cmd[3], cmd[2]) 
            await start_aria_listener(client, query, user_id, cmd[3])
        elif cmd[2] == 'editaria' and STATE == 'view':
            value = aria2_options[cmd[3]]
            if len(value) > 200:
                await query.answer()
                filename = f"{cmd[2]}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f'{value}')
                await sendFile(message, filename)
                return
            elif value == '':
                value = None
            await query.answer(text=f'{value}', show_alert=True)
    elif cmd[1] == "qbit":
        if cmd[2] == 'qbit_menu':
            globals()['START'] = 0
            await edit_menus(message, "qbit")
        elif cmd[2] == "next":
            await query.answer()
            globals()['START'] += 10
            if START > len(qbit_options):
                globals()['START'] = START - 10
            await edit_menus(message, "qbit")
        elif cmd[2] == "back":
            await query.answer()
            globals()['START'] -= 10
            if START < 0:
                globals()['START'] += 10
            await edit_menus(message, "qbit")
        elif cmd[2] == "editqbit" and STATE == 'edit':
            await update_buttons(message, cmd[3], cmd[2]) 
            await start_qbit_listener(client, query, user_id, cmd[3])  
        elif cmd[2] == 'editqbit' and STATE == 'view':
            value = qbit_options[cmd[3]]
            if len(str(value)) > 200:
                await query.answer()
                filename = f"{cmd[2]}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f'{value}')
                await sendFile(message, filename)
                return
            if value == '':
                value = None
            await query.answer(text=f'{value}', show_alert=True)   
    elif cmd[1] == 'edit':
        await query.answer()
        globals()['STATE'] = 'edit'
        await edit_menus(message, cmd[2])
    elif cmd[1] == 'view':
        await query.answer()
        globals()['STATE'] = 'view'
        await edit_menus(message, cmd[2])
    elif cmd[1] == "back":
        await query.answer()
        globals()['START'] = 0
        key = cmd[2] if len(cmd) == 3 else "env"
        await edit_menus(message, key)
    elif cmd[1] == "page":
        await query.answer()
    elif cmd[1] == "close":
        globals()['START'] = 0
        globals()['STATE'] = 'view'
        await query.answer()
        await message.delete()

async def start_aria_listener(client, query, user_id, key):
    message= query.message
    try:
        response = await client.listen.Message(filters.text, id= filters.user(user_id), timeout= 60)
    except TimeoutError:
        await client.send_message(message.chat.id, text="Too late 30s gone, try again!")
        return
    else:
        if response:
            try:
                if "/ignore" in response.text:
                    await client.listen.Cancel(filters.user(user_id))
                    await query.answer("Canceled")
                    return
                else:
                    value= response.text.strip() 
                    if key == 'newkey':
                        key, value = [x.strip() for x in value.split(':', 1)]
                    elif value.lower() == 'true':
                        value = 'true'
                    elif value.lower() == 'false':
                        value = 'false'
                    if key in aria2c_global:
                        aria2.set_global_options({key: value})
                    else:
                        downloads = aria2.get_downloads()
                        if downloads:
                            aria2.set_options({key: value}, downloads)
                    aria2_options[key] = value
                    await edit_menus(message, 'aria')       
            except KeyError:
                return await query.answer("Value doesn't exist") 

async def start_qbit_listener(client, query, user_id, key):
    message= query.message
    try:
        response = await client.listen.Message(filters.text, id= filters.user(user_id), timeout= 60)
    except TimeoutError:
        await client.send_message(message.chat.id, text="Too late 30s gone, try again!")
        return
    else:
        if response:
            try:
                if "/ignore" in response.text:
                    await client.listen.Cancel(filters.user(user_id))
                    await query.answer("Canceled")
                    return
                else:
                    value= response.text.strip() 
                    if value.lower() == 'true':
                        value = True
                    elif value.lower() == 'false':
                        value = False
                    elif key == 'max_ratio':
                        value = float(value)
                    elif value.isdigit():
                        value = int(value)
                    client = get_client()
                    client.app_set_preferences({key: value})
                    qbit_options[key] = value
                    await edit_menus(message, 'qbit')       
            except KeyError:
                return await query.answer("Value doesn't exist") 

async def start_env_listener(client, query, user_id, key, action=""):
    message= query.message
    try:
        response = await client.listen.Message(filters.text, id= filters.user(user_id), timeout= 60)
    except TimeoutError:
        await client.send_message(message.chat.id, text="Too late 30s gone, try again!")
        return
    else:
        if response:
            try:
                if "/ignore" in response.text:
                    await client.listen.Cancel(filters.user(user_id))
                    await query.answer("Canceled")
                    return
                else:
                    value= response.text.strip() 
                    if value.lower() == 'true':
                        value = True
                    elif value.lower() == 'false':
                        value = False
                    elif value.isdigit():
                        value = int(value)
                    elif key == 'STATUS_LIMIT':
                        value = int(value)
                        async with status_reply_dict_lock:
                            try:
                                if Interval:
                                    Interval[0].cancel()
                                    Interval.clear()
                            except:
                                pass
                            finally:
                                Interval.append(setInterval(value, update_all_messages))
                    elif key == 'TORRENT_TIMEOUT':
                        value = int(value)
                        downloads = aria2.get_downloads()
                        if downloads:
                            aria2.set_options({'bt-stop-timeout': f'{value}'}, downloads)
                        aria2_options['bt-stop-timeout'] = f'{value}'
                    elif key == 'DEFAULT_REMOTE':
                        update_rclone_var("MIRRORSET_DRIVE", value, user_id)
                    elif key == 'LEECH_SPLIT_SIZE':
                        value = min(int(value), TG_MAX_FILE_SIZE)
                    elif key == 'SERVER_PORT':
                        value = int(value)
                        srun(["pkill", "-9", "-f", "gunicorn"])
                        Popen(f"gunicorn web.wserver:app --bind 0.0.0.0:{value}", shell=True)
                    elif key == 'EXTENSION_FILTER':
                        fx = value.split()
                        GLOBAL_EXTENSION_FILTER.clear()
                        GLOBAL_EXTENSION_FILTER.append('.aria2')
                        for x in fx:
                            GLOBAL_EXTENSION_FILTER.append(x.strip().lower())
                    elif key == 'SEARCH_API_LINK':
                        initiate_search_tools()
                    elif key == "SUDO_USERS":
                        value= int(value)
                        if action == "rem":
                            SUDO_USERS.remove(value)
                            DbManger().user_rmsudo(value)
                        else:
                            SUDO_USERS.add(value)  
                            DbManger().user_addsudo(value)
                    elif key == "ALLOWED_CHATS":
                        value= int(value)
                        if action == "rem":
                            ALLOWED_CHATS.remove(value)
                            DbManger().user_unauth(value)
                        else:
                            ALLOWED_CHATS.add(value) 
                            DbManger().user_auth(value)
                    config_dict[key] = value
                    environ[key]= str(value)
                    await edit_menus(message, 'env')       
            except KeyError:
                return await query.answer("Value doesn't exist") 

owner_settings_handler = MessageHandler(handle_ownerset, filters= command(BotCommands.OwnerSetCommand) & (CustomFilters.owner_filter))
owner_settings_cb = CallbackQueryHandler(ownerset_callback, filters= regex(r'ownersetmenu'))

bot.add_handler(owner_settings_handler)
bot.add_handler(owner_settings_cb)