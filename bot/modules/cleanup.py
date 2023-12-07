from pyrogram.filters import command, regex
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from asyncio.subprocess import PIPE, create_subprocess_exec as exec
from bot import bot
from bot.helper.ext_utils.menu_utils import Menus
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import editMessage, sendMessage
from bot.helper.ext_utils.rclone_utils import (
    get_rclone_path,
    is_rclone_config,
    list_remotes,
)


async def cleanup(client, message):
    if await is_rclone_config(message.from_user.id, message):
        await list_remotes(message, menu_type=Menus.CLEANUP)


async def cleanup_callback(client, callback_query):
    query = callback_query
    data = query.data
    cmd = data.split("^")
    message = query.message
    tag = f"@{message.reply_to_message.from_user.username}"
    user_id = query.from_user.id

    if int(cmd[-1]) != user_id:
        await query.answer("This menu is not for you!", show_alert=True)
        return
    if cmd[1] == "remote":
        await rclone_cleanup(message, cmd[2], user_id, tag)
    elif cmd[1] == "back":
        await list_remotes(message, menu_type="cleanupmenu", edit=True)
        await query.answer()
    else:
        await query.answer()
        await message.delete()


async def rclone_cleanup(message, remote_name, user_id, tag):
    conf_path = await get_rclone_path(user_id, message)
    msg = "**⏳Cleaning remote trash**\n"
    msg += "\nIt may take some time depending on number of files"
    edit_msg = await editMessage(msg, message)
    cmd = ["rclone", "cleanup", f"--config={conf_path}", f"{remote_name}:"]
    process = await exec(*cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = await process.communicate()
    return_code = await process.wait()
    stdout = stdout.decode().strip()
    if return_code != 0:
        err = stderr.decode().strip()
        await sendMessage(f"Error: {err}", message)
    else:
        msg = "<b>Trash successfully cleaned ✅</b>\n"
        msg += f"<b>cc:</b> {tag}\n"
        await editMessage(msg, edit_msg)


handle_cleanup = MessageHandler(
    cleanup,
    filters=command(BotCommands.CleanupCommand)
    & (CustomFilters.user_filter | CustomFilters.chat_filter),
)
cleanup_cb = CallbackQueryHandler(cleanup_callback, filters=regex("cleanupmenu"))

bot.add_handler(handle_cleanup)
bot.add_handler(cleanup_cb)
