from asyncio import sleep, TimeoutError
from bot import DOWNLOAD_DIR, LOGGER, app, bot
from pyrogram.errors import FloodWait
from pyrogram.errors import ChannelBanned, ChannelInvalid, ChannelPrivate, ChatIdInvalid, ChatInvalid
from pyrogram import filters
from bot.helper.ext_utils.bot_utils import run_async_task
from bot.helper.ext_utils.filters import CustomFilters
from pyrogram.handlers import MessageHandler
from bot.helper.ext_utils.batch_helper import check_link, get_link
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.message_utils import sendMessage
from bot.helper.ext_utils.rclone_utils import is_rclone_config, is_remote_selected
from bot.helper.mirror_leech_utils.download_utils.telegram_downloader import TelegramDownloader
from bot.modules.listener import MirrorLeechListener
from os import path as ospath
from subprocess import run as srun
from bot.modules.mirror_leech import mirror_leech



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
    msg= "Send me one of the followings: \n\n"                
    msg+= "1. Telegram message link from public or private channel\n"        
    msg+= "2. URL links separated each link by new line\n"        
    msg+= "3. TXT file with URL links separated each link by new line\n\n"        
    msg+= "/ignore to cancel"        
    question= await sendMessage(msg, message)
    try:
        response = await client.listen.Message(filters.document | filters.text, id= filters.user(user_id), timeout=60)
        try:
            if response.text:
                if "/ignore" in response.text:
                    await client.listen.Cancel(filters.user(user_id))
                    await question.delete()
                else:
                    lines= response.text.split("\n")  
                    if len(lines) > 1:
                        count= 0
                        for link in lines:
                            link.strip()
                            if link != "\n":
                                count += 1
                            if len(link) > 1:
                                if isLeech:
                                    msg= await bot.send_message(message.chat.id, f"/leech {link}", disable_web_page_preview=True)
                                else:
                                    msg= await bot.send_message(message.chat.id, f"/mirror {link}", disable_web_page_preview=True)
                                msg = await client.get_messages(message.chat.id, msg.id)
                                msg.from_user.id = message.from_user.id
                                run_async_task(mirror_leech, client, msg, isLeech=isLeech)
                                await sleep(4)
                    else:
                        _link = get_link(response.text)
                        await sendMessage("Send me the number of files to save from given link, /ignore to cancel", message)
                        try:
                            _range = await client.listen.Message(filters.text, id= filters.user(user_id), timeout=60)
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
            else:
                file_name = response.document.file_name
                ext= file_name.split(".")[1]
                count= 0
                if ext in ["txt", ".txt"]:
                    if ospath.exists("./links.txt"):
                        srun(["rm", "-rf", "links.txt"])
                    await client.download_media(response, file_name="./links.txt")
                    with open('links.txt', 'r+') as f:
                        lines = f.readlines()
                        for link in lines:
                            link.strip()
                            if link != "\n":
                                count += 1
                            if len(link) > 1:
                                if isLeech:
                                    msg= await bot.send_message(message.chat.id, f"/leech {link}", disable_web_page_preview=True)
                                else:
                                    msg= await bot.send_message(message.chat.id, f"/mirror {link}", disable_web_page_preview=True)
                                msg = await client.get_messages(message.chat.id, msg.id)
                                msg.from_user.id = message.from_user.id
                                run_async_task(mirror_leech, client, msg, isLeech=isLeech)
                                await sleep(4)
                else:
                    await sendMessage("Send a txt file", message)
        except Exception:
            return await sendMessage("No link found.", message)
    except TimeoutError:
        return await sendMessage("Too late 60s gone, try again!", message)

##############################################

# Source: Github.com/Vasusen-code
# Adapted to Pyrogram and Conversation-Pyrogram Library
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
                run_async_task(tg_down.download)
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
                run_async_task(tg_down.download)
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


