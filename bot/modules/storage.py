from configparser import ConfigParser
from json import loads
from pyrogram.filters import command, regex
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.types import InlineKeyboardMarkup
from asyncio.subprocess import PIPE, create_subprocess_exec as exec
from bot import LOGGER, Bot
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.filters import CustomFilters
from bot.helper.ext_utils.human_format import get_readable_file_size
from bot.helper.ext_utils.rclone_utils import is_not_config
from bot.helper.ext_utils.message_utils import editMarkup, sendMarkup, sendMessage
from bot.helper.ext_utils.misc_utils import ButtonMaker, get_rclone_config, pairwise

async def handle_storage(client, message):
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
          buttons.cb_buildsecbutton(f"📁{j}", f"storagemenu^drive^{j}^{user_id}") 

     for a, b in pairwise(buttons.second_button):
          row= [] 
          if b == None:
               row.append(a)  
               buttons.ap_buildbutton(row)
               break
          row.append(a)
          row.append(b)
          buttons.ap_buildbutton(row)

     buttons.cbl_buildbutton("✘ Close Menu", f"storagemenu^close^{user_id}")
    
     if edit:
          await editMarkup("Select cloud to view storage info", message, reply_markup= InlineKeyboardMarkup(buttons.first_button))
     else:
          await sendMarkup("Select cloud to view storage info", message, reply_markup= InlineKeyboardMarkup(buttons.first_button))

async def storage_menu_cb(client, callback_query):
     query= callback_query
     data = query.data
     cmd = data.split("^")
     message = query.message
     user_id= query.from_user.id

     if int(cmd[-1]) != user_id:
          return await query.answer("This menu is not for you!", show_alert=True)

     if cmd[1] == "drive":
          await rclone_about(message, query, cmd[2], user_id)

     elif cmd[1] == "back":
          await list_drive(message, edit=True)
          await query.answer()

     elif cmd[1] == "close":
          await query.answer("Closed")
          await message.delete()     

async def rclone_about(message, query, drive_name, user_id):
     button= ButtonMaker()
     conf_path = get_rclone_config(user_id)
     cmd = ["rclone", "about", "--json", f'--config={conf_path}', f"{drive_name}:"] 
     process = await exec(*cmd, stdout=PIPE, stderr=PIPE)
     stdout, stderr = await process.communicate()
     return_code = await process.wait()
     stdout = stdout.decode().strip()
     if return_code != 0:
          err = stderr.decode().strip()
          return await sendMessage(f'Error: {err}', message)
     info = loads(stdout)
     if len(info) == 0:
          return await query.answer("Team Drive with Unlimited Storage")
     result_msg= "<b>🗂 Storage Details</b>\n"
     try:
          result_msg += f"<b>\nUsed:</b>  {get_readable_file_size(info['used'])} of {get_readable_file_size(info['total'])}"
          result_msg += f"<b>\nFree:</b>  {get_readable_file_size(info['free'])} of {get_readable_file_size(info['total'])}"
          result_msg += f"<b>\nTrashed:</b>  {get_readable_file_size(info['trashed'])}"
     except KeyError:
          result_msg += f"<b>\nN/A:</b>"
     button.cbl_buildbutton("⬅️ Back", f"storagemenu^back^{user_id}")
     button.cbl_buildbutton("✘ Close Menu", f"storagemenu^close^{user_id}")
     await editMarkup(result_msg, message, reply_markup= InlineKeyboardMarkup(button.first_button))

storage_callback= CallbackQueryHandler(storage_menu_cb, filters= regex("storagemenu"))
storage = MessageHandler(handle_storage, filters=command(BotCommands.StorageCommand) & CustomFilters.user_filter | CustomFilters.chat_filter)
Bot.add_handler(storage)
Bot.add_handler(storage_callback)