# Source: Github.com/Vasusen-code
# Adapted to Pyrogram and Conversation-Pyrogram Library

from asyncio import sleep
from bot import DOWNLOAD_DIR, app, bot
from pyrogram.errors import FloodWait
from pyrogram.errors import ChannelBanned, ChannelInvalid, ChannelPrivate, ChatIdInvalid, ChatInvalid
from pyrogram import filters
from bot.helper.ext_utils.filters import CustomFilters
from pyrogram.handlers import MessageHandler
from bot.helper.ext_utils.batch_helper import check_link, get_link
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.message_utils import sendMessage
from bot.helper.ext_utils.rclone_utils import is_rclone_config, is_rclone_drive
from bot.helper.mirror_leech_utils.download_utils.telegram_downloader import TelegramDownloader
from bot.helper.mirror_leech_utils.listener import MirrorLeechListener



async def leech_batch(client, message):
    await _batch(client, message, isLeech=True)

async def mirror_batch(client, message):
    await _batch(client, message)

async def _batch(client, message, isLeech=False):
    user_id= message.from_user.id
    if not isLeech:
        if await is_rclone_config(user_id, message):
            pass
        else:
            return
        if await is_rclone_drive(user_id, message):
            pass
        else:
            return
    if app is None:
        bot= client
    else:
        bot= app
    await sendMessage("Send me the message link to start saving from, /ignore to cancel", message)
    try:
        link = await client.listen.Message(filters.text, id= filters.user(user_id), timeout = 30)
        try:
            if "/ignore" in link.text:
                 return await client.listen.Cancel(filters.user(user_id))
            _link = get_link(link.text)
        except Exception:
            return await sendMessage("No link found.", message)
    except TimeoutError:
        return await sendMessage("Too late 30s gone, try again!", message)
    await sendMessage("Send me the number of files to save from given link, /ignore to cancel", message)
    try:
        _range = await client.listen.Message(filters.text, id= filters.user(user_id), timeout = 30)
        try:
            if "/ignore" in _range.text:
                return await client.listen.Cancel(filters.user(user_id))
            value = int(_range.text)
        except ValueError:
            return await sendMessage("Range must be an integer!", message)
    except TimeoutError:
        return await sendMessage("Too late 30s gone, try again!", message)
    suceed, msg = await check_link(bot, _link)
    if suceed != True:
        await sendMessage(msg, message)
        return
    for i in range(value):
        try:
            await get_bulk_msg(bot, message, _link, i, isLeech=isLeech) 
        except FloodWait as fw:
            await sleep(fw.seconds + 5)
            await get_bulk_msg(bot, message, _link, i, isLeech=isLeech)
        await sleep(5) 

async def get_bulk_msg(bot, message, msg_link, i, isLeech):
    msg_id = int(msg_link.split("/")[-1]) + int(i)
    user_id= message.chat.id
    tag= ''
    if message.from_user.username:
        tag = f"@{message.from_user.username}"
    listener= MirrorLeechListener(message, tag, user_id, isLeech=isLeech)
    if 't.me/c/' in msg_link:
        chat = int('-100' + str(msg_link.split("/")[-2]))
        try:
            msg = await bot.get_messages(chat, msg_id)
            file = msg.document or msg.video or msg.audio or msg.photo or None
            if file is None:
                return
            tg_down= TelegramDownloader(file, bot, listener, f'{DOWNLOAD_DIR}{listener.uid}/', "")
            await tg_down.download() 
        except (ChannelBanned, ChannelInvalid, ChannelPrivate, ChatIdInvalid, ChatInvalid):
            await sendMessage("Have you joined the channel?", message)
        except Exception as e:
            await sendMessage(f'Failed to save: `{e}`', message)
    else:
        chat = msg_link.split("/")[-2]
        try:
            msg = await bot.get_messages(chat, msg_id)
            file = msg.document or msg.video or msg.audio or msg.photo or None
            if file is None:
                return
            tg_down= TelegramDownloader(file, bot, listener, f'{DOWNLOAD_DIR}{listener.uid}/', "")
            await tg_down.download()
        except (ChannelBanned, ChannelInvalid, ChannelPrivate, ChatIdInvalid, ChatInvalid):
            await sendMessage("Have you joined the channel?", message)
            return 
        except Exception as e:
            await sendMessage(f'Failed to save: `{e}`', message)
            return 

mirrorbatch_handler= MessageHandler(mirror_batch, filters=filters.command(BotCommands.MirrorBatchCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter))
leechbatch__handler= MessageHandler(leech_batch, filters=filters.command(BotCommands.LeechBatchCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter))

bot.add_handler(leechbatch__handler)   
bot.add_handler(mirrorbatch_handler)   


