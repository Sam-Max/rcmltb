from asyncio import sleep
from bot import LOGGER, Bot
from pyrogram.errors.exceptions import FloodWait, MessageNotModified

async def sendMessage(text: str, message):
    try:
        return await Bot.send_message(message.chat.id,
                            reply_to_message_id=message.id,
                            text=text)
    except Exception as e:
        LOGGER.error(str(e))

async def sendMarkup(text: str, message, reply_markup):
    try:
        await Bot.send_message(message.chat.id,
                            reply_to_message_id=message.id,
                            text=text, 
                            reply_markup=reply_markup)
    except Exception as e:
        LOGGER.error(str(e))

async def editMarkup(text: str, message, reply_markup):
    try:
        await Bot.edit_message_text(message.chat.id,
                                    message.id,
                                    text=text, 
                                    reply_markup=reply_markup)
    except Exception as e:
        LOGGER.error(str(e))

async def editMessage(text: str, message, reply_markup=None):
    try:
        return await Bot.edit_message_text(text=text, message_id=message.id,
                            chat_id=message.chat.id, reply_markup=reply_markup)
    except FloodWait as fw:
        await sleep(fw.value)
        return await editMessage(text, message, reply_markup)
    except MessageNotModified:
        await sleep(1)
    except Exception as e:
        LOGGER.error(str(e))
        return str(e)

async def deleteMessage(message):
    try:
        await Bot.delete_messages(chat_id=message.chat.id,
                        message_ids=message.id)
    except Exception as e:
        LOGGER.error(str(e))

