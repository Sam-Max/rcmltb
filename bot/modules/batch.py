from asyncio import sleep, TimeoutError
from bot import DOWNLOAD_DIR, LOGGER, app, bot
from pyrogram.errors import FloodWait
from pyrogram import filters
from bot.helper.ext_utils.bot_utils import create_task
from bot.helper.telegram_helper.filters import CustomFilters
from pyrogram.handlers import MessageHandler
from bot.helper.ext_utils.batch_helper import get_link
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.message_utils import sendMessage
from bot.helper.ext_utils.rclone_utils import is_rclone_config, is_remote_selected
from bot.helper.mirror_leech_utils.download_utils.telegram_downloader import TelegramDownloader
from bot.modules.tasks_listener import MirrorLeechListener
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
        if await  is_rclone_config(user_id, message):
            pass
        else: 
            return
        if await is_remote_selected(user_id, message):
            pass
        else: 
            return
    msg= '''
Send me one of the followings:               

1. Telegram message link from public or private channel   

2. URL links separated each link by new line 
   For direct link authorization: 
   link <b>username</b> <b>password</b>

3. TXT file with URL links separated each link by new line        

/ignore to cancel'''       
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
                            args= link.split()
                            if len(args) > 1:
                                user= args[1]
                                if len(args) > 2:
                                    password = args[2]
                                else:
                                    password = ''
                                auth = f"\n{user}\n{password}"
                            else:
                                auth= ''
                            if link != "\n":
                                count += 1
                            if auth:
                                cmd= f"/leech {args[0]}{auth}" if isLeech else f"/mirror {args[0]}{auth}"
                            else:
                                cmd= f"/leech {link}" if isLeech else f"/mirror {link}"  
                            if isLeech:
                                msg= await bot.send_message(message.chat.id, cmd, disable_web_page_preview=True)
                            else:
                                msg= await bot.send_message(message.chat.id, cmd, disable_web_page_preview=True)
                            msg = await client.get_messages(message.chat.id, msg.id)
                            msg.from_user.id = message.from_user.id
                            create_task(mirror_leech, client, msg, isLeech=isLeech)
                            await sleep(4)
                    else:
                        _link = get_link(response.text)
                        await sendMessage("Send me the number of files to save from given link, /ignore to cancel", message)
                        try:
                            _range = await client.listen.Message(filters.text, id= filters.user(user_id), timeout=60)
                            try:
                                if "/ignore" in _range.text:
                                    await client.listen.Cancel(filters.user(user_id))
                                    return
                                else:
                                    multi = int(_range.text)
                            except ValueError:
                                await sendMessage("Range must be an integer!", message)
                                return
                        except TimeoutError:
                            await sendMessage("Too late 60s gone, try again!", message)
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
                                create_task(mirror_leech, client, msg, isLeech=isLeech)
                                await sleep(4)
                else:
                    await sendMessage("Send a txt file", message)
        except Exception:
            await sendMessage("No link found.", message)
    except TimeoutError:
        await sendMessage("Too late 60s gone, try again!", message)

async def get_bulk_msg(message, link, multi, isLeech, value=0):
    msg_id = int(link.split("/")[-1]) + int(value)
    user_id= message.from_user.id

    if username := message.from_user.username:
        tag = f"@{username}"
    else:
        tag = message.from_user.mention

    listener= MirrorLeechListener(message, tag, user_id, isLeech=isLeech)
    
    path= f'{DOWNLOAD_DIR}{listener.uid}/'

    if 't.me/c/' in link:
        if not listener.isSuperGroup:
            await sendMessage('Use SuperGroup to download with User!', listener.message)
            return
        try:
            client= app
            chat = int('-100' + str(link.split("/")[-2]))
            msg = await app.get_messages(chat, msg_id)
        except Exception:
            msg= "Make sure you joined the channel and set USER_SESSION_STRING!!"
            await sendMessage(msg, message)
            return
    else:
        try:
            client= bot
            chat = link.split("/")[-2]
            msg = await bot.get_messages(chat, msg_id)
        except Exception:
            msg= "Bot needs to join chat to download!!"
            await sendMessage(msg, message)
            return
        
    file = msg.document or msg.video or msg.photo or msg.audio or \
           msg.voice or msg.video_note or msg.animation or None
        
    await TelegramDownloader(file, client, listener, path).download()
    await _multi(bot, message, link, value, multi, isLeech)

async def _multi(client, message, link, value, multi, isLeech):
    if multi <= 1:
        return
    try:
        await sleep(4)
        msg = f"/leech {multi - 1}" if isLeech else f"/mirror {multi - 1}"
        nextmsg = await sendMessage(msg, message)
        nextmsg = await client.get_messages(message.chat.id, nextmsg.id)
        nextmsg.from_user = message.from_user
        value += 1
        multi -= 1
        await get_bulk_msg(nextmsg, link, multi, isLeech, value) 
    except FloodWait as fw:
        await sleep(fw.seconds + 5)
        await get_bulk_msg(nextmsg, link, multi, isLeech, value)  


mirrorbatch_handler= MessageHandler(mirror_batch, filters=filters.command(BotCommands.MirrorBatchCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter))
leechbatch__handler= MessageHandler(leech_batch, filters=filters.command(BotCommands.LeechBatchCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter))

bot.add_handler(leechbatch__handler)   
bot.add_handler(mirrorbatch_handler)   


