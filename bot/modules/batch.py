# Source: Github.com/Vasusen-code
# Adapted to Pyrogram and Conversation-Pyrogram Library

from asyncio import sleep, TimeoutError
from bot import DOWNLOAD_DIR, LOGGER, app, bot, botloop
from pyrogram.errors import FloodWait
from pyrogram.errors import ChannelBanned, ChannelInvalid, ChannelPrivate, ChatIdInvalid, ChatInvalid
from pyrogram import filters
from bot.helper.ext_utils.filters import CustomFilters
from pyrogram.handlers import MessageHandler
from bot.helper.ext_utils.batch_helper import check_link, get_link
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.message_utils import sendMessage
from bot.helper.ext_utils.rclone_utils import is_rclone_config, is_remote_selected
from bot.helper.mirror_leech_utils.download_utils.telegram_downloader import TelegramDownloader
from bot.modules.listener import MirrorLeechListener



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
        if await is_remote_selected(user_id, message):
            pass
        else:
            return
    
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
            multi = int(_range.text)
        except ValueError:
            return await sendMessage("Range must be an integer!", message)
    except TimeoutError:
        return await sendMessage("Too late 30s gone, try again!", message)
    suceed, msg = await check_link(_link)
    if suceed != True:
        await sendMessage(msg, message)
        return
    try:
        await get_bulk_msg(message, _link, multi, isLeech=isLeech) 
    except FloodWait as fw:
        await sleep(fw.seconds + 5)
        await get_bulk_msg(message, _link, multi, isLeech=isLeech)

async def get_bulk_msg(message, msg_link, multi, isLeech, value=0):
    msg_id = int(msg_link.split("/")[-1]) + int(value)
    user_id= message.from_user.id
    if message.from_user.username:
        tag = f"@{message.from_user.username}"
    else:
        tag = "N/A"
    if app is not None:
        client= app
    else:
        client= bot
    listener= MirrorLeechListener(message, tag, user_id, isLeech=isLeech)
    if 't.me/c/' in msg_link:
        chat = int('-100' + str(msg_link.split("/")[-2]))
        try:
            if app is not None:
                msg = await client.get_messages(chat, msg_id)
            else:
                msg = await bot.get_messages(chat, msg_id)
            file = msg.document or msg.video or msg.audio or msg.photo or None
            if file is None:
                return
            if multi:
                tg_down= TelegramDownloader(file, client, listener, f'{DOWNLOAD_DIR}{listener.uid}/', "")
                botloop.create_task(tg_down.download()) 
                if multi > 1:
                    msg = f"{multi - 1}"
                    await sleep(4)
                    nextmsg = await sendMessage(msg, message)
                    nextmsg = await bot.get_messages(message.chat.id, nextmsg.id)
                    nextmsg.from_user.id = message.from_user.id
                    value += 1
                    multi -= 1
                    try:
                        await get_bulk_msg(nextmsg, msg_link, multi, isLeech, value) 
                    except FloodWait as fw:
                        await sleep(fw.seconds + 5)
                        await get_bulk_msg(nextmsg, msg_link, multi, isLeech, value)  
        except (ChannelBanned, ChannelInvalid, ChannelPrivate, ChatIdInvalid, ChatInvalid):
            await sendMessage("Have you joined the channel?", message)
        except Exception as e:
            await sendMessage(f'Failed to save: `{e}`', message)
    else:
        chat = msg_link.split("/")[-2]
        try:
            if app is not None:
                msg = await client.get_messages(chat, msg_id)
            else:
                msg = await bot.get_messages(chat, msg_id)
            file = msg.document or msg.video or msg.audio or msg.photo or None
            if file is None:
                return
            if multi:
                tg_down= TelegramDownloader(file, client, listener, f'{DOWNLOAD_DIR}{listener.uid}/', "")
                botloop.create_task(tg_down.download())
                if multi > 1:
                    msg = f"{multi - 1}"
                    await sleep(4)
                    nextmsg = await sendMessage(msg, message)
                    nextmsg = await bot.get_messages(message.chat.id, nextmsg.id)
                    nextmsg.from_user.id = message.from_user.id
                    value += 1
                    multi -= 1
                    try:
                        await get_bulk_msg(nextmsg, msg_link, multi, isLeech, value) 
                    except FloodWait as fw:
                        LOGGER.info("2")
                        await sleep(fw.seconds + 5)
                        await get_bulk_msg(nextmsg, msg_link, multi, isLeech, value)     
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


