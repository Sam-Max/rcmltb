from pyrogram import filters
from pyrogram.handlers import MessageHandler
from bot import bot, app, DOWNLOAD_DIR, LOGGER, user_data, config_dict
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import sendMessage
from bot.helper.ext_utils.bot_utils import new_task
from bot.helper.mirror_leech_utils.download_utils.telegram_downloader import (
    TelegramDownloader,
)
from bot.modules.queue import conditional_queue_add
from bot.modules.tasks_listener import TaskListener
from os import path as ospath


async def private_mirror_handler(client, message):
    """
    Handler for /pmirror command.
    Usage: Reply to a message from a private channel with /pmirror

    Uses the userbot (app) to access messages from private channels
    where the bot doesn't have direct access.
    """
    user_id = message.from_user.id

    if not app:
        await sendMessage(
            "❌ <b>USER_SESSION_STRING not configured!</b>\n\nThis command requires a user session to access private channels.",
            message
        )
        return

    if not message.reply_to_message:
        await sendMessage(
            "❌ <b>Reply to a message from a private channel!</b>\n\nUsage: Reply to a message containing a file with /pmirror",
            message
        )
        return

    # Get the replied message
    replied = message.reply_to_message
    chat_id = replied.chat.id
    message_id = replied.id

    # Check if the message has a file
    file = (
        replied.document
        or replied.video
        or replied.audio
        or replied.photo
        or replied.voice
        or replied.video_note
        or None
    )

    if file is None:
        await sendMessage(
            "❌ <b>No file found in the replied message!</b>",
            message
        )
        return

    # Get file info
    file_name = file.file_name if hasattr(file, "file_name") else "media_file"

    # Check if user can use this feature
    if not await CustomFilters.user_filter("", message) and not await CustomFilters.sudo_filter("", message):
        await sendMessage("⛔ <b>You are not authorized to use this bot!</b>", message)
        return

    # Get username for tagging
    if username := message.from_user.username:
        tag = f"@{username}"
    else:
        tag = message.from_user.mention

    # Prepare listener
    listener = TaskListener(
        message,
        tag,
        user_id,
        compress=None,
        extract=None,
        select=False,
        seed=False,
        isLeech=False,  # Mirror mode by default
        screenshots=None,
        sameDir=None,
    )

    # Set up path
    path = f"{DOWNLOAD_DIR}{message.id}/"

    await sendMessage(
        f"⏳ <b>Starting private channel mirror...</b>\n\n<b>File:</b> <code>{file_name}</code>",
        message
    )

    # Create downloader with userbot
    tgdown = TelegramDownloader(
        file,
        app,  # Use userbot instead of bot
        listener,
        f"{path}/",
    )

    # Override the isSuperGroup check for private channels
    listener.isSuperGroup = True  # Bypass the check

    await conditional_queue_add(message, tgdown.download)


async def private_leech_handler(client, message):
    """
    Handler for /pleech command.
    Usage: Reply to a message from a private channel with /pleech

    Uses the userbot (app) to access messages from private channels
    where the bot doesn't have direct access.
    """
    user_id = message.from_user.id

    if not app:
        await sendMessage(
            "❌ <b>USER_SESSION_STRING not configured!</b>\n\nThis command requires a user session to access private channels.",
            message
        )
        return

    if not message.reply_to_message:
        await sendMessage(
            "❌ <b>Reply to a message from a private channel!</b>\n\nUsage: Reply to a message containing a file with /pleech",
            message
        )
        return

    # Get the replied message
    replied = message.reply_to_message

    # Check if the message has a file
    file = (
        replied.document
        or replied.video
        or replied.audio
        or replied.photo
        or replied.voice
        or replied.video_note
        or None
    )

    if file is None:
        await sendMessage(
            "❌ <b>No file found in the replied message!</b>",
            message
        )
        return

    # Check if user can use this feature
    if not await CustomFilters.user_filter("", message) and not await CustomFilters.sudo_filter("", message):
        await sendMessage("⛔ <b>You are not authorized to use this bot!</b>", message)
        return

    # Get username for tagging
    if username := message.from_user.username:
        tag = f"@{username}"
    else:
        tag = message.from_user.mention

    # Get file info
    file_name = file.file_name if hasattr(file, "file_name") else "media_file"

    # Prepare listener
    listener = TaskListener(
        message,
        tag,
        user_id,
        compress=None,
        extract=None,
        select=False,
        seed=False,
        isLeech=True,  # Leech mode
        screenshots=None,
        sameDir=None,
    )

    # Set up path
    path = f"{DOWNLOAD_DIR}{message.id}/"

    await sendMessage(
        f"⏳ <b>Starting private channel leech...</b>\n\n<b>File:</b> <code>{file_name}</code>",
        message
    )

    # Create downloader with userbot
    tgdown = TelegramDownloader(
        file,
        app,  # Use userbot instead of bot
        listener,
        f"{path}/",
    )

    # Override the isSuperGroup check for private channels
    listener.isSuperGroup = True  # Bypass the check

    await conditional_queue_add(message, tgdown.download)


bot.add_handler(
    MessageHandler(
        private_mirror_handler,
        filters=filters.command(BotCommands.PMirrorCommand)
        & (CustomFilters.user_filter | CustomFilters.chat_filter),
    )
)
bot.add_handler(
    MessageHandler(
        private_leech_handler,
        filters=filters.command(BotCommands.PLeechCommand)
        & (CustomFilters.user_filter | CustomFilters.chat_filter),
    )
)
