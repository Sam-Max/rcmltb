from asyncio import TimeoutError
from os import environ
from pyrogram.filters import regex, command
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from bot import ALLOWED_CHATS, IS_PREMIUM_USER, SUDO_USERS, Bot
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.db_handler import DbManger
from bot.helper.ext_utils.filters import CustomFilters
from bot.helper.ext_utils.human_format import get_readable_file_size
from bot.helper.ext_utils.message_utils import editMarkup, sendMarkup
from bot.helper.ext_utils.misc_utils import ButtonMaker

filter= {"SUDO_USERS", "ALLOWED_CHATS", "DOWNLOAD_DIR", "AUTO_MIRROR", "GDRIVE_FOLDER_ID", "EDIT_SLEEP_SECS", "TORRENT_TIMEOUT","UPTOBOX_TOKEN","UPSTREAM_REPO",
          "UPSTREAM_BRANCH","LEECH_SPLIT_SIZE","AS_DOCUMENT ", "YT_COOKIES_URL", "DATABASE_URL", "DUMP_CHAT","USER_SESSION_STRING", "MEGA_API_KEY","MEGA_EMAIL_ID" ,
          "MEGA_PASSWORD" ,"BASE_URL_OF_BOT","SERVER_PORT", "WEB_PINCODE","SEARCH_API_LINK", "SEARCH_LIMIT"}

list_env_info= []

async def handle_ownerset(client, message):
    text, buttons= await get_ownerset_menu()
    await sendMarkup(text, message, reply_markup= InlineKeyboardMarkup(buttons.first_button))       

async def edit_settings(client, message):
    text, buttons= await get_ownerset_menu()   
    await editMarkup(text, message, reply_markup= InlineKeyboardMarkup(buttons.first_button))

def get_menu_message():
    sudo_users = [f'<code>{i}</code>' for i in SUDO_USERS]
    allowed_chats = [f'<code>{i}</code>' for i in ALLOWED_CHATS]
    sudo_users = f'<code>None</code>' if len(sudo_users) == 0 else sudo_users
    allowed_chats= f'<code>None</code>' if len(allowed_chats) == 0 else allowed_chats

    msg= "❇️<b>Owner Variables Settings</b>"
    msg += "\n\n<b>Here is list of variables:</b>"
    msg += f"\n\n<b>Sudo users:</b> {sudo_users}"
    msg += f"\n<b>Allowed chats:</b> {allowed_chats}"

    dict_env = {key: environ[key] for key in environ.keys() & filter}
    del dict_env["SUDO_USERS"]
    del dict_env["ALLOWED_CHATS"]
    for key, value in dict_env.items():
        if len(value) == 0:
            value= 'None'
        if key == "LEECH_SPLIT_SIZE":
            if value != "None":
                msg += f'\n<b>{key.replace("_", " ").lower().capitalize()}:</b> <code>{value} bytes</code> - ({get_readable_file_size(int(value))})'
            else:
                value= 4194304000 if IS_PREMIUM_USER else 2097152000
                msg += f'\n<b>{key.replace("_", " ").lower().capitalize()}:</b> <code>{value} bytes</code> - ({get_readable_file_size(int(value))})'
        else:
            msg += f'\n<b>{key.replace("_", " ").lower().capitalize()}:</b> <code>{value}</code>'
    msg += "\n\n<b>Notes:</b>"
    msg += "\n1. Use /restart command after you set new values for changes to apply"
    msg += "\n2. Use database for sudo and allowed users to persist when bot restarted"
    
    return msg

async def get_ownerset_menu():
    msg= get_menu_message()
    dict_env_ = {key: environ[key] for key in environ.keys() & filter}
    list_env = sorted(dict_env_.items())
    list_env_info.extend(list_env)

    total = len(list_env)
    max_results= 8
    offset= 0
    start = offset
    end = max_results + start
    next_offset = end

    if end > total:
        list_env= list_env[offset:]    
    elif offset >= total:
        list_env= []    
    else:
        list_env= list_env[start:end]

    buttons= ButtonMaker()    
    for key, value in list_env:
            buttons.dbuildbutton(f"➕ ADD {key}", f"ownersetmenu^change^add^{key}",
                                 f"➖ REMOVE {key}", f"ownersetmenu^change^remove^{key}")

    if offset == 0 and total <= 10:
        buttons.cbl_buildbutton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", data=f"ownersetmenu^pages")        
    else: 
        buttons.dbuildbutton(first_text= f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", first_callback=f"ownersetmenu^pages",
                            second_text= "NEXT ⏩", second_callback= f"ownersetnext {next_offset} back")
    buttons.cbl_buildbutton("✘ Close Menu", f"ownersetmenu^close")
    return msg, buttons

async def ownerset_next(client, callback_query):
    data = callback_query.data
    message= callback_query.message
    _, next_offset, data_back= data.split()
    list_env= list_env_info
    total = len(list_env)
    next_offset = int(next_offset)
    prev_offset = next_offset - 8

    msg= get_menu_message()
    max_results= 8
    start = next_offset
    end = max_results + start
    _next_offset = end

    if end > len(list_env):
        list_env = list_env[start:]    
    elif start >= len(list_env):
        list_env= []    
    else:
        list_env= list_env[start:end] 

    buttons= ButtonMaker()    
    for key, value in list_env:
        buttons.dbuildbutton(f"➕ ADD {key}", f"ownersetmenu^change^add^{key}^",
                             f"➖ REMOVE {key}", f"ownersetmenu^change^remove^{key}")

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
        if cmd[2] == "add":
            await start_listener(client, query, user_id, cmd[3])
            await query.answer()

        elif cmd[2] == "remove":
            if cmd[3] == "SUDO_USERS" or cmd[3] == "ALLOWED_CHATS":
                await start_listener(client, query, user_id, cmd[3], action="rem")
            else:
                environ[cmd[3]]= ""
                await edit_settings(client, message)  
            await query.answer()

    elif cmd[1] == "close":
        await query.answer("Closed")
        await message.delete()

async def start_listener(client, query, user_id, var, action=""):
    message= query.message
    question= await client.send_message(message.chat.id, 
            text= "Send new value for selected variable, /ignore to cancel")
    try:
        response = await client.listen.Message(filters.text, id= filters.user(user_id), timeout = 30)
    except TimeoutError:
        await client.send_message(message.chat.id, text="Too late 30s gone, try again!")
        return
    else:
        if response:
            try:
                if "/ignore" in response.text:
                    await client.listen.Cancel(filters.user(user_id))
                    await query.answer("Canceled")
                else:
                    value= response.text.strip() 
                    if var == "SUDO_USERS":
                        if action == "rem":
                            SUDO_USERS.remove(int(value))
                            DbManger().user_rmsudo(int(value))
                        else:
                            SUDO_USERS.add(int(value))  
                            DbManger().user_addsudo(int(value))
                    elif var == "ALLOWED_CHATS":
                        if action == "rem":
                            ALLOWED_CHATS.remove(int(value))
                            DbManger().user_unauth(int(value))
                        else:
                            ALLOWED_CHATS.add(int(value)) 
                            DbManger().user_auth(int(value))
                    else:
                        environ[var]= value
                    await edit_settings(client, message)       
            except KeyError:
                return await query.answer("Value doesn't exist") 
    finally:
        await question.delete()

owner_settings_handler = MessageHandler(handle_ownerset, filters= command(BotCommands.OwnerSetCommand) & (CustomFilters.owner_filter | CustomFilters.sudo_filter))
owner_settings_cb = CallbackQueryHandler(owner_set_callback, filters= regex(r'ownersetmenu'))
owner_settings_next = CallbackQueryHandler(ownerset_next, filters= regex(r'ownersetnext'))

Bot.add_handler(owner_settings_handler)
Bot.add_handler(owner_settings_cb)
Bot.add_handler(owner_settings_next)