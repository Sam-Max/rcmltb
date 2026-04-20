from asyncio import sleep, TimeoutError
from bot import DOWNLOAD_DIR, app, bot
from bot.helper.ext_utils.help_messages import BATCH_HELP_DICT
from bot.helper.ext_utils.links_utils import is_telegram_link, get_tg_link_message
from bot.helper.ext_utils.exceptions import TgLinkException
from pyrogram.errors import FloodWait
from pyrogram import filters
from pyrogram.types import LinkPreviewOptions
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
    try:
        question = await sendMessage(
            BATCH_HELP_DICT["Cmd"], message, BATCH_HELP_DICT["Menu"]
        )
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
                                message.chat.id, msg, link_preview_options=LinkPreviewOptions(is_disabled=True)
                            )
                        else:
                            msg = await bot.send_message(
                                message.chat.id, msg, link_preview_options=LinkPreviewOptions(is_disabled=True)
                            )
                        msg = await client.get_messages(message.chat.id, msg.id)
                        msg.from_user = message.from_user
                        create_task(mirror_leech, client, msg, isLeech=isLeech)
                        await sleep(7)
                else:
                    _link = get_link(response.text)
                    if _link:
                        await sendMessage(
                            "📋 <b>Send me the number of files to save from given link</b>, /ignore to cancel",
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
                            await sendMessage("❌ <b>Range must be an integer!</b>", message)
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
                                link_preview_options=LinkPreviewOptions(is_disabled=True),
                            )
                        else:
                            msg = await bot.send_message(
                                message.chat.id,
                                f"/mirror {link}",
                                link_preview_options=LinkPreviewOptions(is_disabled=True),
                            )
                        msg = await client.get_messages(message.chat.id, msg.id)
                        msg.from_user = message.from_user.id
                        create_task(mirror_leech, client, msg, isLeech=isLeech)
                        await sleep(7)
            else:
                await sendMessage("📄 <b>Send a .txt file</b>", message)
    except TimeoutError:
        await sendMessage("⏰ Too late 60s gone, try again!", message)
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

    if is_telegram_link(link):
        try:
            msg, client = await get_tg_link_message(link)
        except TgLinkException as e:
            await sendMessage(str(e), message)
            return
    else:
        client = bot
        chat = link.split("/")[-2]
        try:
            msg = await bot.get_messages(chat, msg_id)
        except Exception:
            msg = None
        if msg is None or getattr(msg, 'empty', True):
            if app:
                try:
                    msg = await app.get_messages(chat, msg_id)
                    client = app
                except Exception:
                    await sendMessage("⚠️ <b>Make sure you joined the channel!!</b>", message)
                    return
            else:
                await sendMessage("⚠️ <b>Bot needs to join chat to download!!</b>", message)
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

    if client != bot:
        listener.isSuperGroup = True
        listener.user_transmission = True

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


bot.add_handler(
    MessageHandler(
        mirror_batch,
        filters=filters.command(BotCommands.MirrorBatchCommand)
        & (CustomFilters.user_filter | CustomFilters.chat_filter),
    )
)
bot.add_handler(
    MessageHandler(
        leech_batch,
        filters=filters.command(BotCommands.LeechBatchCommand)
        & (CustomFilters.user_filter | CustomFilters.chat_filter),
    )
)
