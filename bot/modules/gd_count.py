from pyrogram.handlers import MessageHandler
from pyrogram.filters import command
from bot import bot
from bot.helper.mirror_leech_utils.upload_utils.gdriveTools import GoogleDriveHelper
from bot.helper.telegram_helper.message_utils import deleteMessage, sendMessage
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.ext_utils.bot_utils import (
    is_gdrive_link,
    get_readable_file_size,
    run_sync,
)


async def count(_, message):
    args = message.text.split()
    if username := message.from_user.username:
        tag = f"@{username}"
    else:
        tag = message.from_user.mention

    link = args[1] if len(args) > 1 else ""
    if len(link) == 0 and (reply_to := message.reply_to_message):
        link = reply_to.text.split(maxsplit=1)[0].strip()

    if is_gdrive_link(link):
        msg = await sendMessage(f"Counting: <code>{link}</code>", message)
        gd = GoogleDriveHelper()
        name, mime_type, size, files, folders = await run_sync(gd.count, link)
        if mime_type is None:
            await sendMessage(name, message)
            return
        await deleteMessage(msg)
        msg = f"<b>Name: </b><code>{name}</code>"
        msg += f"\n\n<b>Size: </b>{get_readable_file_size(size)}"
        msg += f"\n\n<b>Type: </b>{mime_type}"
        if mime_type == "Folder":
            msg += f"\n<b>SubFolders: </b>{folders}"
            msg += f"\n<b>Files: </b>{files}"
        msg += f"\n\n<b>cc: </b>{tag}"
    else:
        msg = (
            "Send Gdrive link along with command or by replying to the link by command"
        )

    await sendMessage(msg, message)


bot.add_handler(
    MessageHandler(
        count, filters=command(BotCommands.CountCommand) & CustomFilters.user_filter
    )
)
