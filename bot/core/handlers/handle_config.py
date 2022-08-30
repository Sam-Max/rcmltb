import asyncio
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from bot import Bot
from bot.utils.bot_utils.message_utils import sendMessage

@Bot.on_callback_query(filters.regex(r'stop'))
async def _(client, query):
     await query.answer("Closed")
     await client.listen.Cancel(filters.user(query.from_user.id))

async def handle_config(client, message):
     button = InlineKeyboardMarkup([[InlineKeyboardButton('Cancel', callback_data= 'stop')]])
     question= await client.send_message(message.chat.id, 
               reply_to_message_id=message.id,
               text= "Send an Rclone config file", 
               reply_markup= button)
     try:
          response = await client.listen.Message(filters.document, id= filters.user(message.from_user.id), timeout = 30)
     except asyncio.TimeoutError:
          await message.reply("Too late 30s gone.")
     else:
          if response:
               try:
                    await client.download_media(response, file_name= "./rclone.conf")
                    msg = "**Rclone file loaded!**\n"
                    msg += "Use /mirrorset` to select a drive"
                    await sendMessage(msg, message)
               except Exception as ex:
                    await sendMessage(str(ex), message) 
     finally:
          await question.delete()