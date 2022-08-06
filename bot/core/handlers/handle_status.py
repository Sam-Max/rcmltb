
from asyncio import sleep
from bot import status_dict, status_msg_dict
from bot.utils.status_utils.misc_utils import get_bottom_status
from pyrogram.errors.exceptions import FloodWait, MessageNotModified, MessageIdInvalid



async def status_handler(client, message):
          to_edit =  await message.reply_text("**Getting Status...**", quote= True)

          await delete_message(client, int(message.chat.id), int(to_edit.id))

          while True:
                    count = len(status_dict) 
                    status_msg = ""
                    if count == 0:
                         status_msg = 'No Active Downloads !\n___________________________'
                         status_msg += get_bottom_status()
                         await to_edit.edit(status_msg)
                         break
                    else:
                         status_dict_cp = status_dict.copy()
                         for status in list(status_dict_cp.values()):
                              status_msg += status.get_status_msg()
                              status_msg += "_______"
                              status_msg += "\n\n"

                         if len(status_msg) > 3900:
                              await message.reply_text("Message too large to show, try again")
                              await sleep(1)
                         else:
                              try:
                                   await to_edit.edit(status_msg)
                                   await sleep(3)
                              except MessageNotModified:
                                   await sleep(1)
                              except FloodWait as fw:
                                   await sleep(fw.value)
                              except MessageIdInvalid:
                                   break
                         
async def delete_message(client, chat_id, msg_id):                        
     if len(status_msg_dict) == 0:
          status_msg_dict[chat_id]= msg_id
     
     if msg_id != status_msg_dict[chat_id]:
          await client.delete_messages(chat_id, status_msg_dict[chat_id])
          del status_msg_dict[chat_id]
          status_msg_dict[chat_id]= msg_id                       
               
