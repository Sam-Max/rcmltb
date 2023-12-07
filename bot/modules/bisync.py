from pyrogram.filters import command, regex
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from asyncio.subprocess import PIPE, create_subprocess_exec as exec
from bot import bot, config_dict
from bot.helper.ext_utils.menu_utils import Menus
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.ext_utils.rclone_utils import (
    get_rclone_path,
    is_rclone_config,
    list_remotes,
)
from bot.helper.telegram_helper.message_utils import editMarkup, sendMessage
from bot.helper.telegram_helper.button_build import ButtonMaker


sync_dict = {}


async def handle_bisync(client, message):
    user_id = message.from_user.id
    if await is_rclone_config(user_id, message):
        await list_remotes(message, menu_type=Menus.SYNC, remote_type="origin")
        # msg= "Select <b>origin</b> cloud"
        # msg+= "<b>\n\nNote</b>: Bisync check for changes on each side and propagate changes on Origin to Destination, and vice-versa."


async def bysync_cb(client, callbackQuery):
    query = callbackQuery
    data = query.data
    data = data.split("^")
    message = query.message
    user_id = query.from_user.id
    path = await get_rclone_path(user_id, message)

    if data[1] == "origin":
        await query.answer()
        sync_dict["origin"] = data[2]
        await list_remotes(message, menu_type=Menus.SYNC, remote_type="destination")
    elif data[1] == "destination":
        await query.answer()
        sync_dict["destination"] = data[2]
        await start_bisync(message, path)
    else:
        await query.answer()
        await message.delete()


async def start_bisync(message, path):
    origin = sync_dict["origin"]
    destination = sync_dict["destination"]
    if config_dict["SERVER_SIDE"]:
        cmd = [
            "rclone",
            "bisync ",
            "--server-side-across-configs",
            "--remove-empty-dirs",
            "--resync",
            f"--config={path}",
            f"{origin}:",
            f"{destination}:",
        ]
    else:
        cmd = [
            "rclone",
            "bisync",
            "--remove-empty-dirs",
            "--resync",
            f"--config={path}",
            f"{origin}:",
            f"{destination}:",
        ]
    process = await exec(*cmd, stdout=PIPE, stderr=PIPE)
    button = ButtonMaker()
    msg = f"Syncing: {origin} 🔄 {destination}"
    button.cb_buildbutton("Stop", "bisync^stop")
    await editMarkup(msg, message, button.build_menu(1))
    return_code = await process.wait()
    if return_code != 0:
        err = await process.stderr.read()
        msg = f"Error: {err}"
        await sendMessage(msg, message)
    await message.delete()


bisync = MessageHandler(
    handle_bisync,
    filters=command(BotCommands.BiSyncCommand)
    & (CustomFilters.user_filter | CustomFilters.chat_filter),
)
bysync_callback = CallbackQueryHandler(bysync_cb, filters=regex("bisyncmenu"))

bot.add_handler(bisync)
bot.add_handler(bysync_callback)
