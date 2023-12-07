from asyncio import sleep
from time import time
from bot import (
    LOGGER,
    bot,
    Interval,
    app,
    config_dict,
    status_reply_dict_lock,
    status_reply_dict,
)
from pyrogram.errors.exceptions import FloodWait, MessageNotModified
from pyrogram.enums.parse_mode import ParseMode
from bot.helper.ext_utils.bot_utils import get_readable_message, run_sync, setInterval


async def sendMessage(text: str, message, reply_markup=None):
    try:
        return await bot.send_message(
            message.chat.id,
            reply_to_message_id=message.id,
            text=text,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
        )
    except FloodWait as fw:
        await sleep(fw.value * 1.2)
        return await sendMessage(text, message, reply_markup)
    except Exception as e:
        LOGGER.error(str(e))


async def sendPhoto(text, message, path, reply_markup):
    try:
        return await bot.send_photo(
            chat_id=message.chat.id,
            reply_to_message_id=message.id,
            photo=path,
            caption=text,
            reply_markup=reply_markup,
        )
    except FloodWait as fw:
        await sleep(fw.value * 1.2)
        return await sendPhoto(text, message, path, reply_markup)
    except Exception as e:
        LOGGER.error(str(e))


async def sendMarkup(text: str, message, reply_markup):
    try:
        return await bot.send_message(
            message.chat.id,
            reply_to_message_id=message.id,
            text=text,
            reply_markup=reply_markup,
        )
    except FloodWait as fw:
        await sleep(fw.value * 1.2)
        return await sendMarkup(text, message, reply_markup)
    except Exception as e:
        LOGGER.error(str(e))


async def editMarkup(text: str, message, reply_markup):
    try:
        return await bot.edit_message_text(
            message.chat.id, message.id, text=text, reply_markup=reply_markup
        )
    except FloodWait as fw:
        await sleep(fw.value * 1.2)
        return await editMarkup(text, message, reply_markup)
    except MessageNotModified:
        await sleep(1)
    except Exception as e:
        LOGGER.error(str(e))


async def editMessage(text: str, message, reply_markup=None):
    try:
        return await bot.edit_message_text(
            text=text,
            message_id=message.id,
            disable_web_page_preview=True,
            chat_id=message.chat.id,
            reply_markup=reply_markup,
        )
    except FloodWait as fw:
        await sleep(fw.value * 1.2)
        return await editMessage(text, message, reply_markup)
    except MessageNotModified:
        await sleep(1)
    except Exception as e:
        LOGGER.error(str(e))
        return str(e)


async def sendRss(text):
    try:
        if app:
            return await app.send_message(
                chat_id=config_dict["RSS_CHAT_ID"],
                text=text,
                disable_web_page_preview=True,
                disable_notification=True,
            )
        else:
            return await bot.send_message(
                chat_id=config_dict["RSS_CHAT_ID"],
                text=text,
                disable_web_page_preview=True,
                disable_notification=True,
            )
    except FloodWait as f:
        LOGGER.warning(str(f))
        await sleep(f.value * 1.2)
        return await sendRss(text)
    except Exception as e:
        LOGGER.error(str(e))
        return str(e)


async def deleteMessage(message):
    try:
        await bot.delete_messages(chat_id=message.chat.id, message_ids=message.id)
    except Exception as e:
        LOGGER.error(str(e))


async def sendFile(message, file, caption=""):
    try:
        return await bot.send_document(
            document=file,
            reply_to_message_id=message.id,
            caption=caption,
            parse_mode=ParseMode.HTML,
            chat_id=message.chat.id,
        )
    except FloodWait as fw:
        await sleep(fw.value * 1.2)
        return await sendFile(message, file, caption)
    except Exception as e:
        LOGGER.error(str(e))
        return


async def delete_all_messages():
    async with status_reply_dict_lock:
        for key, data in list(status_reply_dict.items()):
            try:
                del status_reply_dict[key]
                await deleteMessage(data[0])
            except Exception as e:
                LOGGER.error(str(e))


async def update_all_messages(force=False):
    async with status_reply_dict_lock:
        if (
            not status_reply_dict
            or not Interval
            or (not force and time() - list(status_reply_dict.values())[0][1] < 3)
        ):
            return
        for chat_id in list(status_reply_dict.keys()):
            status_reply_dict[chat_id][1] = time()
    msg, buttons = await run_sync(get_readable_message)
    if msg is None:
        return
    async with status_reply_dict_lock:
        for chat_id in list(status_reply_dict.keys()):
            if status_reply_dict[chat_id] and msg != status_reply_dict[chat_id][0].text:
                rmsg = await editMessage(msg, status_reply_dict[chat_id][0], buttons)
                if isinstance(rmsg, str) and rmsg.startswith("Telegram says: [400"):
                    del status_reply_dict[chat_id]
                    continue
                status_reply_dict[chat_id][0].text = msg
                status_reply_dict[chat_id][1] = time()


async def sendStatusMessage(msg):
    progress, buttons = await run_sync(get_readable_message)
    if progress is None:
        return
    async with status_reply_dict_lock:
        chat_id = msg.chat.id
        if chat_id in list(status_reply_dict.keys()):
            message = status_reply_dict[chat_id][0]
            await deleteMessage(message)
            del status_reply_dict[chat_id]
        message = await sendMarkup(progress, msg, buttons)
        message.text = progress
        status_reply_dict[chat_id] = [message, time()]
        if not Interval:
            Interval.append(
                setInterval(config_dict["STATUS_UPDATE_INTERVAL"], update_all_messages)
            )


async def auto_delete_message(cmd_message=None, bot_message=None):
    if config_dict["AUTO_DELETE_MESSAGE_DURATION"] != -1:
        await sleep(config_dict["AUTO_DELETE_MESSAGE_DURATION"])
        if cmd_message is not None:
            await deleteMessage(cmd_message)
        if bot_message is not None:
            await deleteMessage(bot_message)
