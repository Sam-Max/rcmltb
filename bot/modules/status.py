
from asyncio import sleep
from bot import Bot, status_dict, status_reply_dict, status_dict_lock, status_reply_dict_lock
from pyrogram.handlers import MessageHandler
from pyrogram import filters
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.filters import CustomFilters
from bot.helper.ext_utils.message_utils import auto_delete_message, deleteMessage, editMessage, sendMessage

from bot.helper.mirror_leech_utils.status_utils.status_utils import get_bottom_status

UP_MSG_LOOP= []

async def status_handler(client, message):
          chat_id= message.chat.id
          async with status_dict_lock:
               count = len(status_dict)
          if count == 0:
               status_msg = "**No Active Processes**\n"
               status_msg += get_bottom_status()
               msg= await sendMessage(status_msg, message)
               await auto_delete_message(msg, message)
          else:
               async with status_dict_lock:
                    status_msg= ""
                    for download in list(status_dict.values()):
                         status_msg += download.get_status_msg()
                         status_msg += "_"
                         status_msg += "\n\n"
               
               if len(status_msg) == 0:
                    return
               elif len(status_msg) > 3900:
                    return

               async with status_reply_dict_lock:
                    if chat_id in status_reply_dict:
                         await deleteMessage(status_reply_dict[chat_id][0])
                         del status_reply_dict[chat_id] 
                    
                    try:
                         if UP_MSG_LOOP:
                              UP_MSG_LOOP[0].cancel()
                              UP_MSG_LOOP.clear()
                    except:
                         pass

                    edit_message = await sendMessage(status_msg, message)
                    status_reply_dict[chat_id] = [edit_message]

               up_msg = UpdateMessageLoop(chat_id, edit_message)
               if not UP_MSG_LOOP:
                    UP_MSG_LOOP.append(up_msg)
               await up_msg.update()
               
class UpdateMessageLoop:
     def __init__(self, chat_id, message):
          self.chat_id= chat_id
          self.message= message
          self.stop_loop= False

     async def update(self):
          while True:
               async with status_reply_dict_lock:
                    if not status_reply_dict or not UP_MSG_LOOP:
                         return
               async with status_dict_lock:
                    count = len(status_dict)
               if count == 0:
                    await deleteMessage(self.message)
                    return 
               if self.stop_loop:
                    return 
               async with status_dict_lock:
                    status_msg= ""
                    for download in list(status_dict.values()):
                         status_msg += download.get_status_msg()
                         status_msg += "_"
                         status_msg += "\n\n"
               async with status_reply_dict_lock:
                    if status_reply_dict[self.chat_id] and status_msg != status_reply_dict[self.chat_id][0].text:
                         await editMessage(status_msg, status_reply_dict[self.chat_id][0])
                         status_reply_dict[self.chat_id][0].text = status_msg
               await sleep(2)

     def cancel(self):
          self.stop_loop= True
                         

status_handlers = MessageHandler(status_handler,filters= filters.command(BotCommands.StatusCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter))
Bot.add_handler(status_handlers)    
