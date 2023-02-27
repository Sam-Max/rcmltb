from configparser import ConfigParser
from pyrogram.filters import command, regex
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from asyncio.subprocess import PIPE, create_subprocess_exec as exec
from bot import bot
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.filters import CustomFilters
from bot.helper.ext_utils.message_utils import editMarkup, editMessage, sendMarkup, sendMessage
from bot.helper.ext_utils.button_build import ButtonMaker
from bot.helper.ext_utils.rclone_utils import get_rclone_config, is_rclone_config



async def cleanup(client, message):
     if await is_rclone_config(message.from_user.id, message):
          await list_remotes(message)

async def list_remotes(message, edit= False):
     if message.reply_to_message:
        user_id= message.reply_to_message.from_user.id
     else:
        user_id= message.from_user.id

     buttons = ButtonMaker()
     conf_path = get_rclone_config(user_id)
     conf = ConfigParser()
     conf.read(conf_path)

     for remote in conf.sections():
          buttons.cb_buildbutton(f"📁{remote}", f"cleanupmenu^drive^{remote}^{user_id}") 

     buttons.cb_buildbutton("✘ Close Menu", f"cleanupmenu^close^{user_id}", 'footer')
    
     if edit:
          await editMarkup("Select cloud to delete trash", message, reply_markup= buttons.build_menu(2))
     else:
          await sendMarkup("Select cloud to delete trash", message, reply_markup= buttons.build_menu(2))

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
          await list_remotes(message, edit=True)
          await query.answer()

     elif cmd[1] == "close":
          await query.answer()
          await message.delete()     

async def rclone_cleanup(message, drive_name, user_id, tag):
     conf_path = get_rclone_config(user_id)
     msg= "**⏳Cleaning remote trash**\n"
     msg += "\nIt may take some time depending on number of files"
     edit_msg= await editMessage(msg, message)
     cmd = ["rclone", "cleanup", f'--config={conf_path}', f"{drive_name}:"] 
     process = await exec(*cmd, stdout=PIPE, stderr=PIPE)
     stdout, stderr = await process.communicate()
     return_code = await process.wait()
     stdout = stdout.decode().strip()
     if return_code != 0:
          err = stderr.decode().strip()
          return await sendMessage(f'Error: {err}', message)
     msg= "<b>Trash successfully cleaned ✅</b>\n"
     msg+= f'<b>cc:</b> {tag}\n'
     await editMessage(msg, edit_msg)     


handle_cleanup = MessageHandler(cleanup, filters=command(BotCommands.CleanupCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter))
cleanup_cb= CallbackQueryHandler(cleanup_callback, filters= regex("cleanupmenu"))

bot.add_handler(handle_cleanup)
bot.add_handler(cleanup_cb)