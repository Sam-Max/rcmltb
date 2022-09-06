import asyncio
from pyrogram.filters import regex, command
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from bot import Bot
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from os import path as ospath, getcwd
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.filters import CustomFilters
from bot.helper.ext_utils.message_utils import sendMessage

async def _(client, query):
     await query.answer("Closed")
     await client.listen.Cancel(filters.user(query.from_user.id))

async def handle_config(client, message):
     user_id= message.from_user.id
     button = InlineKeyboardMarkup([[InlineKeyboardButton('Cancel', callback_data= 'stop')]])
     question= await client.send_message(message.chat.id, 
               reply_to_message_id=message.id,
               text= "Send an Rclone config file", 
               reply_markup= button)
     try:
          response = await client.listen.Message(filters.document | filters.user(message.from_user.id), id= filters.user(message.from_user.id), timeout = 30)
     except asyncio.TimeoutError:
          await message.reply("Too late 30s gone.")
     else:
          if response:
               try:
                    path = ospath.join(getcwd(), "users", str(user_id), "rclone.conf" )
                    await client.download_media(response, file_name=path)
                    msg = "Use /mirrorset` to select a drive"
                    await sendMessage(msg, message)
               except Exception as ex:
                    await sendMessage(str(ex), message) 
     finally:
          await question.delete()

config_handler = MessageHandler(handle_config, filters= command(BotCommands.ConfigCommand) & CustomFilters.user_filter | CustomFilters.chat_filter)
but_set_handler = CallbackQueryHandler(_, filters= regex(r'stop'))

Bot.add_handler(config_handler)
Bot.add_handler(but_set_handler)