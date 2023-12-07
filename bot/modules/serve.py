from asyncio import create_subprocess_exec
from configparser import ConfigParser
from bot import LOGGER, OWNER_ID, bot, config_dict
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from asyncio.subprocess import PIPE
from pyrogram import filters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.ext_utils.bot_utils import cmd_exec
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import editMarkup, sendMarkup
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.rclone_utils import get_rclone_path, is_rclone_config


SELECTED_REMOTE = []
process_dict = {"status": "inactive", "pid": None}


async def serve(client, message):
    if await is_rclone_config(message.from_user.id, message):
        if process_dict["status"] == "inactive":
            await list_remotes(message)
        else:
            button = ButtonMaker()
            url = f"{config_dict['RC_INDEX_URL']}:{config_dict['RC_INDEX_PORT']}"
            msg = f"Serving on <a href={url}>{url}</a>"
            button.cb_buildbutton("Stop", "servemenu^stop")
            await sendMarkup(msg, message, button.build_menu(1))


async def serve_callback(client, query):
    message = query.message
    data = query.data.split("^")
    path = await get_rclone_path(OWNER_ID)

    RC_INDEX_USER = config_dict["RC_INDEX_USER"]
    RC_INDEX_PASS = config_dict["RC_INDEX_PASS"]
    RC_INDEX_PORT = config_dict["RC_INDEX_PORT"]

    if data[1] == "remote":
        SELECTED_REMOTE.append(data[2])
        button = ButtonMaker()
        button.cb_buildbutton("HTTP", "servemenu^http")
        button.cb_buildbutton("WEBDAV", "servemenu^webdav")
        await editMarkup(
            "Choose protocol to serve the remote", message, button.build_menu(2)
        )
    elif data[1] == "all":
        cmd = [
            "rclone",
            "rcd",
            "--rc-serve",
            f"--rc-addr=:{RC_INDEX_PORT}",
            f"--rc-user={RC_INDEX_USER}",
            f"--rc-pass={RC_INDEX_PASS}",
            f"--config={path}",
        ]
        await rclone_serve(cmd, message)
    elif data[1] == "http":
        cmd = [
            "rclone",
            "serve",
            "http",
            f"--addr=:{RC_INDEX_PORT}",
            f"--user={RC_INDEX_USER}",
            f"--pass={RC_INDEX_PASS}",
            f"--config={path}",
            f"{SELECTED_REMOTE[0]}:",
        ]
        await rclone_serve(cmd, message)
    elif data[1] == "webdav":
        cmd = [
            "rclone",
            "serve",
            "webdav",
            f"--addr=:{RC_INDEX_PORT}",
            f"--user={RC_INDEX_USER}",
            f"--pass={RC_INDEX_PASS}",
            f"--config={path}",
            f"{SELECTED_REMOTE[0]}:",
        ]
        await rclone_serve(cmd, message)
    elif data[1] == "stop":
        _, stderr, return_code = await cmd_exec(
            ["kill", "-9", f"{process_dict['pid']}"]
        )
        if return_code == 0:
            await query.answer(text="Server stopped", show_alert=True)
            process_dict["status"] = "inactive"
            await message.delete()
        else:
            LOGGER.info(f"Error: {stderr}")
            process_dict["status"] = "active"
    else:
        await query.answer()
        await message.delete()


async def rclone_serve(cmd, message):
    button = ButtonMaker()
    url = f"{config_dict['RC_INDEX_URL']}:{config_dict['RC_INDEX_PORT']}"
    msg = f"Serving on <a href={url}>{url}</a>"
    msg += f"\n<b>User</b>: <code>{config_dict['RC_INDEX_USER']}</code>"
    msg += f"\n<b>Pass</b>: <code>{config_dict['RC_INDEX_PASS']}</code>"
    button.cb_buildbutton("Stop", "servemenu^stop")
    await editMarkup(msg, message, button.build_menu(1))

    process = await create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
    process_dict["pid"] = process.pid
    process_dict["status"] = "active"
    _, stderr = await process.communicate()
    stderr = stderr.decode().strip()

    if process.returncode != 0:
        LOGGER.info(f"Error: {stderr}")
        process_dict["status"] = "inactive"


async def list_remotes(message):
    SELECTED_REMOTE.clear()
    button = ButtonMaker()
    path = await get_rclone_path(OWNER_ID)
    conf = ConfigParser()
    conf.read(path)
    for remote in conf.sections():
        button.cb_buildbutton(f"📁{remote}", f"servemenu^remote^{remote}")
    button.cb_buildbutton("🌐 All", "servemenu^all")
    button.cb_buildbutton("✘ Close Menu", "servemenu^close")
    await sendMarkup(
        "Select cloud to serve as index", message, reply_markup=button.build_menu(2)
    )


serve_handler = MessageHandler(
    serve,
    filters=filters.command(BotCommands.ServeCommand)
    & (CustomFilters.owner_filter | CustomFilters.chat_filter),
)
serve_cb_handler = CallbackQueryHandler(
    serve_callback, filters=filters.regex("servemenu")
)

bot.add_handler(serve_handler)
bot.add_handler(serve_cb_handler)
