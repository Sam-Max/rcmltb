from asyncio import sleep
from os import remove
from bot import LOGGER, Bot
from pyrogram.errors.exceptions import FloodWait, MessageNotModified
from pyrogram.enums.parse_mode import ParseMode


async def sendMessage(text: str, message):
    try:
        return await Bot.send_message(message.chat.id, reply_to_message_id=message.id,
                            text=text, disable_web_page_preview=True)
    except FloodWait as fw:
        await sleep(fw.value)
        return await sendMessage(text, message)
    except Exception as e:
        LOGGER.error(str(e))

async def sendMarkup(text: str, message, reply_markup):
    try:
        return await Bot.send_message(message.chat.id,
                            reply_to_message_id=message.id,
                            text=text, 
                            reply_markup=reply_markup)
    except FloodWait as fw:
        await sleep(fw.value)
        return await sendMarkup(text, message, reply_markup)
    except Exception as e:
        LOGGER.error(str(e))

async def editMarkup(text: str, message, reply_markup):
    try:
        return await Bot.edit_message_text(message.chat.id,
                                    message.id,
                                    text=text, 
                                    reply_markup=reply_markup)
    except FloodWait as fw:
        await sleep(fw.value)
        return await editMarkup(text, message, reply_markup) 
    except MessageNotModified:
        await sleep(1)                               
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

async def sendFile(message, name: str, caption=""):
    try:
        with open(name, 'rb') as f:
            await Bot.send_document(document=f, file_name=f.name, reply_to_message_id=message.id,
                             caption=caption, parse_mode=ParseMode.HTML, chat_id=message.chat.id)
        remove(name)
        return
    except FloodWait as fw:
        await sleep(fw.value)
        return await sendFile(message, name, caption)
    except Exception as e:
        LOGGER.error(str(e))
        return

async def auto_delete_message(cmd_message, bot_message):
        await sleep(20)
        try:
            # Skip if None is passed meaning we don't want to delete bot or cmd message
            await deleteMessage(cmd_message)
            await deleteMessage(bot_message)
        except AttributeError:
            pass