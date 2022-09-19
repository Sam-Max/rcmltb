from asyncio import TimeoutError
from pyrogram.filters import regex, command
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from bot import ALLOWED_CHATS, ALLOWED_USERS, IS_PREMIUM_USER, Bot
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.filters import CustomFilters
from bot.helper.ext_utils.message_utils import editMarkup, sendMarkup
from bot.helper.ext_utils.misc_utils import ButtonMaker
from bot.helper.ext_utils.var_holder import get_config_var, set_config_var



async def owner_settings_callback(client, callback_query):
    query= callback_query
    data = query.data
    cmd = data.split("^")
    message = query.message
    user_id= query.from_user.id

    if int(cmd[-1]) != user_id:
        return await query.answer("This menu is not for you!", show_alert=True)

    if cmd[1] == "change":
        if cmd[2] == "adduser":
            await start_listener(client, query, user_id, ALLOWED_USERS)
        elif cmd[2] == "removeuser":
            await start_listener(client, query, user_id, ALLOWED_USERS, action="rem")
        elif cmd[2] == "addchat":
            await start_listener(client, query, user_id, ALLOWED_CHATS)
        elif cmd[2] == "removechat":
            await start_listener(client, query, user_id, ALLOWED_CHATS, action="rem")
        elif cmd[2] == "adddumpchat":
            await start_listener(client, query, user_id, "DUMP_CHAT", type="dic")
        elif cmd[2] == "removedumpchat":
             set_config_var("DUMP_CHAT", None)  
             await edit_settings(client, message) 
        elif cmd[2] == "addsplit":
             await start_listener(client, query, user_id, "TG_SPLIT_SIZE", type="dic")
        elif cmd[2] == "removesplit":
             TG_MAX_FILE_SIZE= 4194304000 if IS_PREMIUM_USER else 2097152000
             set_config_var("TG_SPLIT_SIZE", TG_MAX_FILE_SIZE)  
             await edit_settings(client, message)  
        elif cmd[2] == "adduptobox":
             await start_listener(client, query, user_id, "UPTOBOX_TOKEN", type="dic")
        elif cmd[2] == "remuptobox":
             set_config_var("UPTOBOX_TOKEN", None)  
             await edit_settings(client, message)  
        await query.answer()

    if cmd[1] == "close":
        await query.answer("Closed")
        await message.delete()

async def get_settings(client, message):
    if message.reply_to_message:
        user_id= message.reply_to_message.from_user.id
    else:
        user_id= message.from_user.id
    users= [f'<code>{i}</code>' for i in ALLOWED_USERS]
    chats= [f'<code>{i}</code>' for i in ALLOWED_CHATS]
    dump_chat= get_config_var("DUMP_CHAT")
    split_size= get_config_var("TG_SPLIT_SIZE")
    uptobox_token= get_config_var("UPTOBOX_TOKEN")
    msg= "❇️<b>Owner Variables Settings</b>"
    msg+= "\n\n<b>Here is list of variables:</b>"
    msg+= f"\n\n<b>Allowed users:</b> {users}"
    msg+= f"\n<b>Allowed chats:</b> {chats}"
    msg+= f"\n<b>Dump chat:</b> <code>{dump_chat}</code>"
    msg+= f"\n<b>Split size:</b> <code>{split_size}</code>"
    msg+= f"\n<b>Uptobox token:</b> <code>{uptobox_token}</code>"

    buttons= ButtonMaker()
    buttons.dbuildbutton("➕ ADD USER", f"settingsmenu^change^adduser^{user_id}",
                         "➖ REMOVE USER", f"settingsmenu^change^removeuser^{user_id}")
    buttons.dbuildbutton("➕ ADD CHAT", f"settingsmenu^change^addchat^{user_id}",
                         "➖ REMOVE CHAT", f"settingsmenu^change^removechat^{user_id}")
    buttons.dbuildbutton("➕ ADD DUMP CHAT", f"settingsmenu^change^adddumpchat^{user_id}",
                         "➖ REMOVE DUMP CHAT", f"settingsmenu^change^removedumpchat^{user_id}")
    buttons.dbuildbutton("➕ ADD SPLIT SIZE", f"settingsmenu^change^addsplit^{user_id}",
                         "➖ REMOVE SPLIT SIZE", f"settingsmenu^change^removesplit^{user_id}")  
    buttons.dbuildbutton("➕ ADD UPTOBOX TOKEN", f"settingsmenu^change^adduptobox^{user_id}",
                         "➖ REMOVE UPTOBOX TOKEN", f"settingsmenu^change^remuptobox^{user_id}")                    
    buttons.cbl_buildbutton("✘ Close Menu", f"settingsmenu^close^{user_id}")
    return msg, buttons
    
async def handle_owner_setting(client, message):
    text, buttons= await get_settings(client, message)
    await sendMarkup(text, message, reply_markup= InlineKeyboardMarkup(buttons.first_button))       

async def edit_settings(client, message):
    text, buttons= await get_settings(client, message)   
    await editMarkup(text, message, reply_markup= InlineKeyboardMarkup(buttons.first_button))

async def start_listener(client, query, user_id, var, action="", type=""):
    message= query.message
    question= await client.send_message(message.chat.id, 
            text= "Send new value for variable, /ignore to cancel")
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
                    if type == "dic":   
                        if var == "UPTOBOX_TOKEN":
                            value= response.text.strip() 
                        else:
                            value= int(response.text.strip())    
                        set_config_var(var, value)
                    else:
                        if action == "rem":
                            var.remove(int(response.text.strip()))
                        else:
                            var.add(int(response.text.strip()))  
                    await edit_settings(client, message)   
            except KeyError:
                return await query.answer("Value doesn't exist") 
            except ValueError:
                return await query.answer("Value is not correct")
    finally:
        await question.delete()
        await response.delete()

owner_settings_handler = MessageHandler(handle_owner_setting, filters= command(BotCommands.OwnerSetCommand) & CustomFilters.owner_filter | CustomFilters.chat_filter)
owner_settings_cb = CallbackQueryHandler(owner_settings_callback, filters= regex(r'settingsmenu'))

Bot.add_handler(owner_settings_handler)
Bot.add_handler(owner_settings_cb)