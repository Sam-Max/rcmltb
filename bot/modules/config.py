from asyncio import TimeoutError
from asyncio.subprocess import PIPE, create_subprocess_exec as exec
from pyrogram.filters import regex, command
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from os import path as ospath
from bot import DB_URI, Bot
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.db_handler import DbManger
from bot.helper.ext_utils.filters import CustomFilters
from bot.helper.ext_utils.message_utils import sendMarkup, sendMessage
from bot.helper.ext_utils.misc_utils import ButtonMaker, get_rclone_config



async def config_callback(client, callback_query):
     query= callback_query
     data = query.data
     cmd = data.split("^")
     message = query.message
     user_id= query.from_user.id

     if int(cmd[-1]) != user_id:
          return await query.answer("This menu is not for you!", show_alert=True)

     if cmd[1] == "get_config":
          path= get_rclone_config(user_id)
          try:
               await client.send_document(document=path, chat_id=message.chat.id)
          except ValueError as err:
               await sendMessage(str(err), message)
          await query.answer()

     if cmd[1] == "get_pickle":
          try:
               await client.send_document(document="token.pickle", chat_id=message.chat.id)
          except ValueError as err:
               await sendMessage(str(err), message)
          await query.answer()

     if cmd[1] == "change_config":
          await query.answer()
          await set_config_listener(client, message, is_rclone=True)

     if cmd[1] == "change_pickle":
          await query.answer()
          await set_config_listener(client, message)

     if cmd[1] == "close":
        await query.answer("Closed")
        await message.delete()

async def handle_config(client, message):
     user_id= message.from_user.id
     conf_path= get_rclone_config(user_id)
     buttons= ButtonMaker()
     fstr= ''
     if conf_path is not None and ospath.exists(conf_path):
          cmd = ["rclone", "listremotes", f'--config={conf_path}'] 
          process = await exec(*cmd, stdout=PIPE, stderr=PIPE)
          stdout, stderr = await process.communicate()
          return_code = await process.wait()
          stdout = stdout.decode().strip()
          info= stdout.split("\n")
          for i in info:
              rstr = i.replace(":", "")
              fstr += f"- {rstr}\n"
          if return_code != 0:
               err = stderr.decode().strip()
               return await sendMessage(f'Error: {err}', message)  
     msg= "❇️ **Rclone configuration**"
     msg+= "\n\n**Here is list of drives in config file:**"
     msg+= f"\n{fstr}"
     path= ospath.join("users", str(user_id), "rclone.conf")
     if ospath.exists(path):
          buttons.dbuildbutton("🗂 Get rclone.conf", f"configmenu^get_config^{user_id}",
                              "📃 Change rclone.conf", f"configmenu^change_config^{user_id}")
     else:
          buttons.cbl_buildbutton("📃 Load rclone.conf", f"configmenu^change_config^{user_id}")
     if ospath.exists("token.pickle"):
          buttons.dbuildbutton("🗂 Get token.pickle", f"configmenu^get_pickle^{user_id}",
                              "📃 Change token.pickle", f"configmenu^change_pickle^{user_id}")
     else:
          buttons.cbl_buildbutton("📃 Load token.pickle", f"configmenu^change_pickle^{user_id}")
     buttons.cbl_buildbutton("✘ Close Menu", f"configmenu^close^{user_id}")
     await sendMarkup(msg, message, reply_markup= InlineKeyboardMarkup(buttons.first_button))

async def set_config_listener(client, message, is_rclone= False):
     if message.reply_to_message:
          user_id= message.reply_to_message.from_user.id
     else:
          user_id= message.from_user.id

     question= await client.send_message(message.chat.id, 
               text= "Send file, /ignore to cancel")
     try:
          response = await client.listen.Message(filters.document | filters.text, id= filters.user(user_id), timeout = 30)
     except TimeoutError:
          await client.send_message(message.chat.id, text="Too late 30s gone, try again!")
     else:
          if response:
               try:
                    if response.text:
                        if "/ignore" in response.text:
                            await client.listen.Cancel(filters.user(user_id))
                    else:
                         if is_rclone:
                              rclone_path = ospath.join("users", str(user_id), "rclone.conf" )
                              path= await client.download_media(response, file_name=rclone_path)
                              if DB_URI is not None:
                                   DbManger().user_saveconfig(user_id, path)
                              msg = "Use /mirrorset to select a drive"
                              await sendMessage(msg, message)
                         else:
                              path= await client.download_media(response, file_name= "./")
                              if DB_URI is not None:
                                   DbManger().user_savepickle(user_id, path)
               except Exception as ex:
                    await sendMessage(str(ex), message) 
     finally:
          await question.delete()

config_handler = MessageHandler(handle_config, filters= command(BotCommands.ConfigCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter))
config_cb = CallbackQueryHandler(config_callback, filters= regex(r'configmenu'))

Bot.add_handler(config_handler)
Bot.add_handler(config_cb)