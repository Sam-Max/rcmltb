from pyrogram.handlers import MessageHandler
from pyrogram import filters
from bot.uploaders.rclone.rclone_clone import GDriveClone
from bot.utils.bot_commands import BotCommands
from bot.utils.bot_utils.message_utils import sendMessage
from bot import Bot
from bot.utils.bot_utils.bot_utils import is_gdrive_link

async def _clone(client, message):
     user_id= message.from_user.id
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
          msg += "For folder: <code>/gdrive</code> link | folder name\n"
          msg += "For file: <code>/gdrive</code> link"
          await sendMessage(msg, message) 

clone_handler = MessageHandler(
     _clone,
     filters= filters.command(BotCommands.GcloneCommand))
Bot.add_handler(clone_handler)