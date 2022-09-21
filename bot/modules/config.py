from asyncio import TimeoutError
from asyncio.subprocess import PIPE, create_subprocess_exec as exec
from pyrogram.filters import regex, command
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from os import path as ospath
from bot import DB_URI, LOGGER, Bot
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.db_handler import DbManger
from bot.helper.ext_utils.filters import CustomFilters
from bot.helper.ext_utils.message_utils import sendMarkup, sendMessage
from bot.helper.ext_utils.misc_utils import ButtonMaker, get_rclone_config

async def stop(client, query):
     await client.listen.Cancel(filters.user(query.from_user.id))
     await query.answer("Canceled")
     await query.message.delete()

async def config_callback(client, callback_query):
     query= callback_query
     data = query.data
     cmd = data.split("^")
     message = query.message
     user_id= query.from_user.id

     if int(cmd[-1]) != user_id:
          return await query.answer("This menu is not for you!", show_alert=True)

     if cmd[1] == "get":
          path= get_rclone_config(user_id)
          await client.send_document(document=path, chat_id=message.chat.id)
          await query.answer()

     if cmd[1] == "change":
          await query.answer()
          await set_config_listener(client, message)

     if cmd[1] == "close":
        await query.answer("Closed")
        await message.delete()

async def handle_config(client, message):
     user_id= message.from_user.id
     conf_path= get_rclone_config(user_id)
     buttons= ButtonMaker()
     if conf_path is not None and ospath.exists(conf_path):
          cmd = ["rclone", "listremotes", f'--config={conf_path}'] 
          process = await exec(*cmd, stdout=PIPE, stderr=PIPE)
          stdout, stderr = await process.communicate()
          return_code = await process.wait()
          stdout = stdout.decode().strip()
          info= stdout.split("\n")
          fstr= ''
          for i in info:
              rstr = i.replace(":", "")
              fstr += f"- {rstr}\n"
          if return_code != 0:
               err = stderr.decode().strip()
               return await sendMessage(f'Error: {err}', message)  
          msg= "❇️ **Rclone configuration**"
          msg+= "\n\n**Here is list of drives in config file:**"
          msg+= f"\n{fstr}"
          buttons.cbl_buildbutton("🗂 Get rclone config", f"configmenu^get^{user_id}")
          buttons.cbl_buildbutton("📃 Change rclone config", f"configmenu^change^{user_id}")
          buttons.cbl_buildbutton("✘ Close Menu", f"configmenu^close^{user_id}")
          await sendMarkup(msg, message, reply_markup= InlineKeyboardMarkup(buttons.first_button))       
     else:
          await set_config_listener(client, message)  

async def set_config_listener(client, message):
     if message.reply_to_message:
          user_id= message.reply_to_message.from_user.id
     else:
          user_id= message.from_user.id

     button = InlineKeyboardMarkup([[InlineKeyboardButton('Cancel', callback_data= 'stop')]])
     question= await client.send_message(message.chat.id, 
               text= "Send an Rclone config file", 
               reply_markup= button)
     try:
          response = await client.listen.Message(filters.document, id= filters.user(user_id), timeout = 30)
     except TimeoutError:
          await client.send_message(message.chat.id, text="Too late 30s gone, try again!")
     else:
          if response:
               try:
                    rc_path = ospath.join("users", str(user_id), "rclone.conf" )
                    path= await client.download_media(response, file_name=rc_path)
                    if DB_URI is not None:
                         DbManger().user_save_rcconfig(user_id, path)
                    msg = "Use /mirrorset to select a drive"
                    await sendMessage(msg, message)
               except Exception as ex:
                    await sendMessage(str(ex), message) 
     finally:
          await question.delete()

config_handler = MessageHandler(handle_config, filters= command(BotCommands.ConfigCommand) & CustomFilters.user_filter | CustomFilters.chat_filter)
stop_cb = CallbackQueryHandler(stop, filters= regex(r'stop'))
config_cb = CallbackQueryHandler(config_callback, filters= regex(r'configmenu'))

Bot.add_handler(config_handler)
Bot.add_handler(stop_cb)
Bot.add_handler(config_cb)