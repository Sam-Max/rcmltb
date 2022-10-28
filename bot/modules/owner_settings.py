from asyncio import TimeoutError
from os import environ
from subprocess import Popen, run as srun
from pyrogram.filters import regex, command
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from bot import ALLOWED_CHATS, GLOBAL_EXTENSION_FILTER, SUDO_USERS, TG_MAX_FILE_SIZE, bot, Interval, aria2, config_dict, status_reply_dict_lock
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.bot_utils import setInterval 
from bot.helper.ext_utils.db_handler import DbManger
from bot.helper.ext_utils.filters import CustomFilters
from bot.helper.ext_utils.human_format import get_readable_file_size
from bot.helper.ext_utils.message_utils import editMarkup, sendMarkup, update_all_messages
from bot.helper.ext_utils.misc_utils import ButtonMaker
from bot.modules.search import initiate_search_tools


listener = {}

default_values = {'AUTO_DELETE_MESSAGE_DURATION': 30,
                  'UPSTREAM_BRANCH': 'master',
                  'STATUS_UPDATE_INTERVAL': 10,
                  'LEECH_SPLIT_SIZE': TG_MAX_FILE_SIZE,
                  'SEARCH_LIMIT': 0,
                  'SERVER_PORT': 80,
                  'RSS_DELAY': 900}

async def handle_ownerset(client, message):
    text, buttons= await get_ownerset_menu()
    await sendMarkup(text, message, reply_markup= InlineKeyboardMarkup(buttons.first_button))       

async def edit_settings(client, message):
    text, buttons= await get_ownerset_menu()   
    await editMarkup(text, message, reply_markup= InlineKeyboardMarkup(buttons.first_button))

def get_menu_message():
    msg= "❇️<b>Config Variables Settings</b>"
    msg += "\n\n<b>Here is list of variables:</b>"
    for key, value in config_dict.items():
        if key == "LEECH_SPLIT_SIZE":
            msg += f'\n<b>{key.replace("_", " ").lower().capitalize()}:</b> <code>{value} bytes</code> - ({get_readable_file_size(int(value))})'
        else:
            msg += f'\n<b>{key.replace("_", " ").lower().capitalize()}:</b> <code>{value}</code>'
    msg += "\n\n<b>Notes:</b>"
    msg += "\n1. Use database for sudo and allowed users to persist when bot restarted"
    msg += "\n2. OWNER_ID, BOT_TOKEN, DOWNLOAD_DIR and DATABASE_URL, are non-editable while bot is running"
    return msg

async def get_ownerset_menu():
    msg= get_menu_message()
    config_list= list(sorted(config_dict.items()))
    listener['config_list'] = config_list
    total = len(config_list)
    max_results= 10
    offset= 0
    start = offset
    end = max_results + start
    next_offset = end

    if end > total:
        list_env= config_list[offset:]    
    elif offset >= total:
        list_env= []    
    else:
        list_env= config_list[start:end]

    buttons= ButtonMaker()    
    for key, _ in list_env:
            if key in ['ALLOWED_CHATS', 'SUDO_USERS']:
                buttons.dbuildbutton(f"➕ {key}", f"ownersetmenu^change^add^{key}",
                                     f"➖ DELETE {key}", f"ownersetmenu^change^reset^{key}")
            else:
                buttons.dbuildbutton(f"➕ {key}", f"ownersetmenu^change^add^{key}",
                                     f"➖ RESET {key}", f"ownersetmenu^change^reset^{key}")

    if offset == 0 and total <= 10:
        buttons.cbl_buildbutton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", data=f"ownersetmenu^pages")        
    else: 
        buttons.dbuildbutton(first_text= f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", first_callback=f"ownersetmenu^pages",
                            second_text= "NEXT ⏩", second_callback= f"ownersetnext {next_offset} back")
    buttons.cbl_buildbutton("✘ Close Menu", f"ownersetmenu^close")
    return msg, buttons

async def ownerset_next(client, callback_query):
    query= callback_query
    data = query.data
    message= query.message
    await query.answer()
    _, next_offset, data_back= data.split()
    config_list = listener['config_list'] 
    total = len(config_list)
    next_offset = int(next_offset)
    prev_offset = next_offset - 10

    msg= get_menu_message()
    max_results= 10
    start = next_offset
    end = max_results + start
    _next_offset = end

    if end > len(config_list):
        list_env = config_list[start:]    
    elif start >= len(config_list):
        list_env= []    
    else:
        list_env= config_list[start:end] 

    buttons= ButtonMaker()    
    for key, value in list_env:
        if key in ['ALLOWED_CHATS', 'SUDO_USERS']:
            buttons.dbuildbutton(f"➕ {key}", f"ownersetmenu^change^add^{key}",
                                 f"➖ DELETE {key}", f"ownersetmenu^change^reset^{key}")
        else:
            buttons.dbuildbutton(f"➕ {key}", f"ownersetmenu^change^add^{key}",
                                 f"➖ RESET {key}", f"ownersetmenu^change^reset^{key}")

    if next_offset == 0:
        buttons.dbuildbutton(first_text = f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", first_callback="ownersetmenu^pages", 
                            second_text= "NEXT ⏩", second_callback= f"ownersetnext {_next_offset} {data_back}" )
    
    elif next_offset >= total:
        buttons.dbuildbutton(first_text="⏪ BACK", first_callback= f"ownersetnext {prev_offset} {data_back}", 
                        second_text=f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", second_callback="ownersetmenu^pages")
   
    elif next_offset + 10 > total:
        buttons.dbuildbutton(first_text="⏪ BACK", first_callback= f"ownersetnext {prev_offset} {data_back}", 
                        second_text= f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", second_callback="ownersetmenu^pages")                               
    else:
        buttons.tbuildbutton(first_text="⏪ BACK", first_callback= f"ownersetnext {prev_offset} {data_back}", 
                            second_text= f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", second_callback="ownersetmenu^pages",
                            third_text="NEXT ⏩", third_callback=f"ownersetnext {_next_offset} {data_back}")

    buttons.cbl_buildbutton("✘ Close Menu", f"ownersetmenu^close")
    await editMarkup(msg, message, reply_markup= InlineKeyboardMarkup(buttons.first_button))

async def owner_set_callback(client, callback_query):
    query= callback_query
    data = query.data
    cmd = data.split("^")
    message = query.message
    user_id= query.from_user.id

    if cmd[1] == "change":
        if cmd[3] in ['RSS_USER_SESSION_STRING', 'AUTO_MIRROR', 'CMD_INDEX', 'USER_SESSION_STRING', 
                            'TELEGRAM_API_HASH', 'TELEGRAM_API_ID', 'RSS_DELAY']:
                await query.answer(text='Restart required for this to apply!', show_alert=True)
        if cmd[2] == "add":
            await query.answer()
            await start_listener(client, query, user_id, cmd[3])
        elif cmd[2] == "reset":
            await query.answer()
            value = ''
            if cmd[3] == "SUDO_USERS" or cmd[3] == "ALLOWED_CHATS":
                await start_listener(client, query, user_id, cmd[3], action="rem")
            elif cmd[3] in default_values:
                value = default_values[cmd[3]]
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
            config_dict[cmd[3]] = value
            environ[cmd[3]]= str(value)
            await edit_settings(client, message)  

    elif cmd[1] == "close":
        await query.answer("Closed")
        await message.delete()

async def start_listener(client, query, user_id, key, action=""):
    message= query.message
    question= await client.send_message(message.chat.id, 
              text= "Send new value for selected variable, /ignore to cancel. Timeout: 60 sec")
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
                        config_dict[key] = value
                    elif value.lower() == 'false':
                        value = False
                        config_dict[key] = value    
                    elif value.isdigit():
                        value = int(value)
                        config_dict[key] = value
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
                        config_dict[key] = value
                        aria2.set_global_options({'bt-stop-timeout': value})
                    elif key == 'LEECH_SPLIT_SIZE':
                        value = int(value)
                        value = min(value, TG_MAX_FILE_SIZE)
                        config_dict[key] = value
                    elif key == 'SERVER_PORT':
                        value = int(value)
                        srun(["pkill", "-9", "-f", "gunicorn"])
                        Popen(f"gunicorn web.wserver:app --bind 0.0.0.0:{value}", shell=True)
                        config_dict[key] = value
                    elif key == 'EXTENSION_FILTER':
                        fx = value.split()
                        GLOBAL_EXTENSION_FILTER.clear()
                        GLOBAL_EXTENSION_FILTER.append('.aria2')
                        for x in fx:
                            GLOBAL_EXTENSION_FILTER.append(x.strip().lower())
                        config_dict[key] = value
                    elif key == 'SEARCH_API_LINK':
                        config_dict[key] = value
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
                    else:
                        config_dict[key] = value
                    environ[key]= str(value)
                    await edit_settings(client, message)       
            except KeyError:
                return await query.answer("Value doesn't exist") 
    finally:
        await question.delete()

owner_settings_handler = MessageHandler(handle_ownerset, filters= command(BotCommands.OwnerSetCommand) & (CustomFilters.owner_filter | CustomFilters.sudo_filter))
owner_settings_cb = CallbackQueryHandler(owner_set_callback, filters= regex(r'ownersetmenu'))
owner_settings_next = CallbackQueryHandler(ownerset_next, filters= regex(r'ownersetnext'))

bot.add_handler(owner_settings_handler)
bot.add_handler(owner_settings_cb)
bot.add_handler(owner_settings_next)