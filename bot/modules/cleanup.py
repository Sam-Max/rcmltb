from configparser import ConfigParser
from pyrogram.filters import command, regex
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.types import InlineKeyboardMarkup
from asyncio.subprocess import PIPE, create_subprocess_exec as exec
from bot import Bot
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.filters import CustomFilters
from bot.helper.ext_utils.rclone_utils import is_not_config
from bot.helper.ext_utils.message_utils import editMarkup, editMessage, sendMarkup, sendMessage
from bot.helper.ext_utils.misc_utils import ButtonMaker, get_rclone_config, pairwise

async def handle_cleanup(client, message):
     if await is_not_config(message.from_user.id, message):
          return  
     await list_drive(message)

async def list_drive(message, edit= False):
     if message.reply_to_message:
        user_id= message.reply_to_message.from_user.id
     else:
        user_id= message.from_user.id

     buttons = ButtonMaker()
     conf_path = get_rclone_config(user_id)
     conf = ConfigParser()
     conf.read(conf_path)

     for j in conf.sections():
          buttons.cb_buildsecbutton(f"📁{j}", f"cleanupmenu^drive^{j}^{user_id}") 

     for a, b in pairwise(buttons.second_button):
          row= [] 
          if b == None:
               row.append(a)  
               buttons.ap_buildbutton(row)
               break
          row.append(a)
          row.append(b)
          buttons.ap_buildbutton(row)

     buttons.cbl_buildbutton("✘ Close Menu", f"cleanupmenu^close^{user_id}")
    
     if edit:
          await editMarkup("Select cloud to delete trash", message, reply_markup= InlineKeyboardMarkup(buttons.first_button))
     else:
          await sendMarkup("Select cloud to delete trash", message, reply_markup= InlineKeyboardMarkup(buttons.first_button))

async def cleanup_callback(client, callback_query):
     query= callback_query
     data = query.data
     cmd = data.split("^")
     message = query.message
     tag = f"@{message.reply_to_message.from_user.username}"
     user_id= query.from_user.id

     if int(cmd[-1]) != user_id:
          return await query.answer("This menu is not for you!", show_alert=True)

     if cmd[1] == "drive":
          await rclone_cleanup(message, cmd[2], user_id, tag)

     elif cmd[1] == "back":
          await list_drive(message, edit=True)
          await query.answer()

     elif cmd[1] == "close":
          await query.answer("Closed")
          await message.delete()     

async def rclone_cleanup(message, drive_name, user_id, tag):
     conf_path = get_rclone_config(user_id)
     edit_msg= await editMessage("⏳ Cleaning remote trash", message)
     cmd = ["rclone", "cleanup", f'--config={conf_path}', f"{drive_name}:"] 
     process = await exec(*cmd, stdout=PIPE, stderr=PIPE)
     stdout, stderr = await process.communicate()
     return_code = await process.wait()
     stdout = stdout.decode().strip()
     if return_code != 0:
          err = stderr.decode().strip()
          return await sendMessage(f'Error: {err}', message)
     msg= "<b>Trash Cleared</b>\n\n"
     msg+= f'<b>cc:</b> {tag}\n'
     await editMessage(msg, edit_msg)     

cleanup_callback= CallbackQueryHandler(cleanup_callback, filters= regex("cleanupmenu"))
cleanup = MessageHandler(handle_cleanup, filters=command(BotCommands.CleanupCommand) & CustomFilters.user_filter | CustomFilters.chat_filter)
Bot.add_handler(cleanup_callback)
Bot.add_handler(cleanup)