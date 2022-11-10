from asyncio import TimeoutError
from asyncio.subprocess import PIPE, create_subprocess_exec as exec
from pyrogram.filters import regex, command
from pyrogram import filters
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from os import path as ospath, remove
from subprocess import run as srun
from bot import DB_URI, LOGGER, OWNER_ID, bot, config_dict
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.db_handler import DbManger
from bot.helper.ext_utils.filters import CustomFilters
from bot.helper.ext_utils.message_utils import sendMarkup, sendMessage
from bot.helper.ext_utils.misc_utils import ButtonMaker, get_rclone_config

async def handle_config(client, message):
     user_id= message.from_user.id
     if config_dict['MULTI_RCLONE_CONFIG']: 
          await config_menu(user_id, message)    
     else:
        if user_id == OWNER_ID:  
          await config_menu(user_id, message) 
        else:
          await sendMessage("You can't use on current mode", message)

async def config_callback(client, callback_query):
     query= callback_query
     data = query.data
     cmd = data.split("^")
     message = query.message
     user_id= query.from_user.id

     if int(cmd[-1]) != user_id:
          return await query.answer("This menu is not for you!", show_alert=True)

     elif cmd[1] == "get_config":
          path= get_rclone_config(user_id)
          try:
               await client.send_document(document=path, chat_id=message.chat.id)
          except ValueError as err:
               await sendMessage(str(err), message)
          await query.answer()

     elif cmd[1] == "get_pickle":
          try:
               await client.send_document(document="token.pickle", chat_id=message.chat.id)
          except ValueError as err:
               await sendMessage(str(err), message)
          await query.answer()

     elif cmd[1] == "change_config":
          await query.answer()
          await set_config_listener(client, message, True)

     elif cmd[1] == "change_pickle":
          await query.answer()
          await set_config_listener(client, message)

     elif cmd[1] == "change_acc":
          await query.answer()
          await set_config_listener(client, message)

     elif cmd[1] == "close":
        await query.answer()
        await message.delete()

async def config_menu(user_id, message ):
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
          buttons.cb_buildbutton("🗂 Get rclone.conf", f"configmenu^get_config^{user_id}")
          buttons.cb_buildbutton("📃Change rclone.conf", f"configmenu^change_config^{user_id}")
     else:
          buttons.cb_buildbutton("📃 Load rclone.conf", f"configmenu^change_config^{user_id}")
     if ospath.exists("token.pickle"):
          buttons.cb_buildbutton("🗂 Get token.pickle", f"configmenu^get_pickle^{user_id}")
          buttons.cb_buildbutton("📃 Change token.pickle", f"configmenu^change_pickle^{user_id}")
     else:
          buttons.cb_buildbutton("📃 Load token.pickle", f"configmenu^change_pickle^{user_id}")
     buttons.cb_buildbutton("📃 Load accounts.zip", f"configmenu^change_acc^{user_id}")
     buttons.cb_buildbutton("✘ Close Menu", f"configmenu^close^{user_id}", 'footer')
     await sendMarkup(msg, message, reply_markup= buttons.build_menu(2))

async def set_config_listener(client, message, is_rclone=False):
     if message.reply_to_message:
          user_id= message.reply_to_message.from_user.id
     else:
          user_id= message.from_user.id
     question= await client.send_message(message.chat.id, text= "Send file, /ignore to cancel")
     try:
          response = await client.listen.Message(filters.document | filters.text, id= filters.user(user_id), timeout = 30)
     except TimeoutError:
          await client.send_message(message.chat.id, text="Too late 30s gone, try again!")
     else:
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
                         await client.send_message(message.chat.id, text="Select a drive now, use /mirrorset")
                    else:
                         file_name = response.document.file_name
                         path= await client.download_media(response, file_name='./')
                         if file_name == 'accounts.zip':
                              srun(["unzip", "-q", "-o", "accounts.zip"])
                              srun(["chmod", "-R", "777", "accounts"])
                         elif file_name == "token.pickle":
                              if DB_URI is not None:
                                   DbManger().user_savepickle(user_id, path)
                         if ospath.exists('accounts.zip'):
                              remove('accounts.zip')
          except Exception as ex:
               await sendMessage(str(ex), message) 
     finally:
          await question.delete()

config_handler = MessageHandler(handle_config, filters= command(BotCommands.ConfigCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter))
config_cb = CallbackQueryHandler(config_callback, filters= regex(r'configmenu'))

bot.add_handler(config_handler)
bot.add_handler(config_cb)