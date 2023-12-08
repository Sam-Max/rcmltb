from random import SystemRandom
from string import ascii_letters, digits
from pyrogram.filters import command, regex
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from asyncio.subprocess import PIPE, create_subprocess_exec as exec
from bot import bot, config_dict, status_dict_lock, status_dict
from bot.helper.ext_utils.menu_utils import Menus
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.ext_utils.rclone_utils import (
    get_rclone_path,
    is_rclone_config,
    list_remotes,
)
from bot.helper.telegram_helper.message_utils import sendStatusMessage
from bot.modules.tasks_listener import TaskListener
from bot.helper.mirror_leech_utils.status_utils.sync_status import SyncStatus


SOURCE = None
listener_dict = {}


async def handle_sync(client, message):
    user_id = message.from_user.id
    tag = f"@{message.from_user.username}"
    if await is_rclone_config(user_id, message):
        await list_remotes(message, menu_type=Menus.SYNC, remote_type="source")
        listener_dict[message.id] = TaskListener(message, tag, user_id)


async def sync_callback(client, query):
    data = query.data.split("^")
    message = query.message
    user_id = query.from_user.id
    msg_id = query.message.reply_to_message.id

    listener = listener_dict[msg_id]
    path = await get_rclone_path(user_id, message)

    if data[1] == "source":
        await query.answer()
        globals()["SOURCE"] = data[2]
        await list_remotes(
            message, menu_type=Menus.SYNC, remote_type="destination", edit=True
        )
    elif data[1] == "destination":
        await query.answer()
        destination = data[2]
        await start_sync(message, path, destination, listener)
    else:
        await query.answer()
        await message.delete()


async def start_sync(message, path, destination, listener):
    cmd = [
        "rclone",
        "sync",
        "--delete-during",
        "-P",
        f"--config={path}",
        f"{SOURCE}:",
        f"{destination}:",
    ]
    if config_dict["SERVER_SIDE"]:
        cmd.append("--server-side-across-configs")

    process = await exec(*cmd, stdout=PIPE, stderr=PIPE)

    gid = "".join(SystemRandom().choices(ascii_letters + digits, k=10))
    async with status_dict_lock:
        status = SyncStatus(process, gid, SOURCE, destination, listener)
        status_dict[listener.uid] = status
    await sendStatusMessage(listener.message)
    await status.start()

    return_code = await process.wait()

    if return_code == 0:
        msg = "Sync completed successfully✅\n\n"
        msg += "<b>Note:</b>"
        msg += "\n1.Use dedupe command to remove duplicate file/directory"
        msg += "\n2.Use rmdir command to remove empty directories"
        await listener.onRcloneSyncComplete(msg)
    else:
        err = await process.stderr.read()
        await listener.onDownloadError(str(err))

    await message.delete()


bot.add_handler(
    MessageHandler(
        handle_sync,
        filters=command(BotCommands.SyncCommand)
        & (CustomFilters.user_filter | CustomFilters.chat_filter),
    )
)

bot.add_handler(CallbackQueryHandler(sync_callback, filters=regex("syncmenu")))
