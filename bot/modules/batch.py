from asyncio import sleep, TimeoutError
from bot import DOWNLOAD_DIR, app, bot
from pyrogram.errors import FloodWait
from pyrogram import filters
from bot.helper.ext_utils.bot_utils import create_task, new_task
from bot.helper.telegram_helper.filters import CustomFilters
from pyrogram.handlers import MessageHandler
from bot.helper.ext_utils.batch_helper import get_link
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.message_utils import deleteMessage, sendMessage
from bot.helper.ext_utils.rclone_utils import is_rclone_config, is_remote_selected
from bot.helper.mirror_leech_utils.download_utils.telegram_downloader import (
    TelegramDownloader,
)
from bot.modules.tasks_listener import TaskListener
from os import path as ospath
from subprocess import run as srun
from bot.modules.mirror_leech import mirror_leech


async def leech_batch(client, message):
    await _batch(client, message, isLeech=True)


async def mirror_batch(client, message):
    await _batch(client, message)


async def _batch(client, message, isLeech=False):
    user_id = message.from_user.id
    if not isLeech:
        if not await is_rclone_config(user_id, message):
            return
        if not await is_remote_selected(user_id, message):
            return
    msg = """
Send me one of the followings:               

1. <b>Telegram Link</b> 
   Public: https://t.me/channel_name/message_id
   Private: https://t.me/c/channel_id/message_id

2. <b>URL links</b> 
   Each link separated by new line 
   Direct link authorization: link username password

3. <b>TXT file</b> 
   Each link inside txt separated by new line        

/ignore to cancel"""
    try:
        question = await sendMessage(msg, message)
        response = await client.listen.Message(
            filters.document | filters.text, id=filters.user(user_id), timeout=60
        )
        if response.text:
            if "/ignore" in response.text:
                pass
            else:
                lines = response.text.split("\n")
                if len(lines) > 1:
                    username = ""
                    password = ""
                    for link in lines:
                        args = link.split()
                        if len(args) > 1:
                            username = args[1]
                            if len(args) > 2:
                                password = args[2]
                            auth = True
                        else:
                            auth = False
                        if auth:
                            msg = (
                                f"/leech {args[0]} -au {username} -ap {password}"
                                if isLeech
                                else f"/mirror {args[0]} -au {username} -ap {password}"
                            )
                        else:
                            msg = f"/leech {link}" if isLeech else f"/mirror {link}"
                        if isLeech:
                            msg = await bot.send_message(
                                message.chat.id, msg, disable_web_page_preview=True
                            )
                        else:
                            msg = await bot.send_message(
                                message.chat.id, msg, disable_web_page_preview=True
                            )
                        msg = await client.get_messages(message.chat.id, msg.id)
                        msg.from_user = message.from_user
                        create_task(mirror_leech, client, msg, isLeech=isLeech)
                        await sleep(7)
                else:
                    _link = get_link(response.text)
                    await sendMessage(
                        "Send me the number of files to save from given link, /ignore to cancel",
                        message,
                    )
                    try:
                        response = await client.listen.Message(
                            filters.text, id=filters.user(user_id), timeout=60
                        )
                        if "/ignore" in response.text:
                            return
                        else:
                            multi = int(response.text)
                        await download(message, _link, multi, isLeech=isLeech)
                    except ValueError:
                        await sendMessage("Range must be an integer!", message)
                    except FloodWait as fw:
                        await sleep(fw.seconds + 5)
                        await download(message, _link, multi, isLeech=isLeech)
        else:
            file_name = response.document.file_name
            if file_name.split(".")[1] in ["txt", ".txt"]:
                if ospath.exists("./links.txt"):
                    srun(["rm", "-rf", "links.txt"])
                path = await client.download_media(response, file_name="./links.txt")
                with open(path, "r+") as f:
                    lines = f.readlines()
                for link in lines:
                    if len(link.strip()) > 1:
                        if isLeech:
                            msg = await bot.send_message(
                                message.chat.id,
                                f"/leech {link}",
                                disable_web_page_preview=True,
                            )
                        else:
                            msg = await bot.send_message(
                                message.chat.id,
                                f"/mirror {link}",
                                disable_web_page_preview=True,
                            )
                        msg = await client.get_messages(message.chat.id, msg.id)
                        msg.from_user = message.from_user.id
                        create_task(mirror_leech, client, msg, isLeech=isLeech)
                        await sleep(7)
            else:
                await sendMessage("Send a txt file", message)
    except TimeoutError:
        await sendMessage("Too late 60s gone, try again!", message)
    finally:
        await deleteMessage(question)


async def download(message, link, multi, isLeech, value=0):
    msg_id = int(link.split("/")[-1]) + value
    user_id = message.from_user.id

    if username := message.from_user.username:
        tag = f"@{username}"
    else:
        tag = message.from_user.mention

    listener = TaskListener(message, tag, user_id, isLeech=isLeech)

    path = f"{DOWNLOAD_DIR}{listener.uid}/"

    if "t.me/c/" in link:
        if not app:
            await sendMessage("You need to set USER_SESSION_STRING!!", message)
            return
        try:
            client = app
            chat = int("-100" + link.split("/")[-2])
            msg = await app.get_messages(chat, msg_id)
        except Exception:
            await sendMessage("Make sure you joined the channel!!", message)
            return
    else:
        client = bot
        chat = link.split("/")[-2]
        msg = await bot.get_messages(chat, msg_id)
        if msg.empty:
            if app:
                client = app
                try:
                    msg = await app.get_messages(chat, msg_id)
                except Exception:
                    await sendMessage("Make sure you joined the channel!!", message)
                    return
            else:
                await sendMessage("Bot needs to join chat to download!!", message)
                return

    _multi(message, link, value, multi, isLeech)

    file = (
        msg.document
        or msg.video
        or msg.photo
        or msg.audio
        or msg.voice
        or msg.video_note
        or msg.sticker
        or msg.animation
        or None
    )

    await TelegramDownloader(file, client, listener, path).download()


@new_task
async def _multi(message, link, value, multi, isLeech):
    if multi <= 1:
        return
    try:
        await sleep(4)
        msg = f"/leech -i {multi - 1}" if isLeech else f"/mirror -i {multi - 1}"
        nextmsg = await sendMessage(msg, message)
        nextmsg = await bot.get_messages(message.chat.id, nextmsg.id)
        nextmsg.from_user = message.from_user
        value += 1
        multi -= 1
        await download(nextmsg, link, multi, isLeech, value)
    except FloodWait as fw:
        await sleep(fw.seconds + 5)
        await download(nextmsg, link, multi, isLeech, value)


mirrorbatch_handler = MessageHandler(
    mirror_batch,
    filters=filters.command(BotCommands.MirrorBatchCommand)
    & (CustomFilters.user_filter | CustomFilters.chat_filter),
)
leechbatch__handler = MessageHandler(
    leech_batch,
    filters=filters.command(BotCommands.LeechBatchCommand)
    & (CustomFilters.user_filter | CustomFilters.chat_filter),
)

bot.add_handler(leechbatch__handler)
bot.add_handler(mirrorbatch_handler)
