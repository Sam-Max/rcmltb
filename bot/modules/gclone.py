from pyrogram.handlers import MessageHandler
from pyrogram import filters
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.bot_utils import is_gdrive_link
from bot.helper.ext_utils.filters import CustomFilters
from bot.helper.ext_utils.message_utils import sendMessage
from bot import Bot
from bot.helper.ext_utils.rclone_utils import is_not_config, is_not_drive
from bot.helper.mirror_leech_utils.download_utils.rclone.rclone_clone import GDriveClone

async def _clone(client, message):
     user_id= message.from_user.id
     if await is_not_config(user_id, message):
          return
     if await is_not_drive(user_id, message):
          return
     reply_to = message.reply_to_message
     args = message.text.split("|", maxsplit=1)
     if len(args) > 1:
          link = args[0].strip()
          name = args[1].strip()
     else:
          link = message.text
          name = "" 
     if reply_to:
          args= reply_to.text.split("|", maxsplit=1)
          if len(args) > 1:
               link = args[0].strip()
               name = args[1].strip()
          else:
               link = reply_to.text
               name = ""  
     if is_gdrive_link(link):
          glcone= GDriveClone(message, user_id, link, name)
          await glcone.clone()  
     else:
          msg= "<b>Send Gdrive link with command or replying to the link</b>\n\n"
          msg += "For folder: <code>/clone</code> link | folder name\n"
          msg += "For file: <code>/clone</code> link"
          await sendMessage(msg, message) 

clone_handler = MessageHandler(_clone,
     filters= filters.command(BotCommands.GcloneCommand) & CustomFilters.user_filter | CustomFilters.chat_filter)
     
Bot.add_handler(clone_handler)