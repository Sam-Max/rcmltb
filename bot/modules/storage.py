from html import escape as html_escape
from json import loads
from math import floor
from pyrogram.filters import command, regex
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from asyncio.subprocess import PIPE, create_subprocess_exec as exec
from bot import bot
from bot.helper.ext_utils.menu_utils import Menus
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.ext_utils.human_format import get_readable_file_size
from bot.helper.ext_utils.rclone_utils import (
    get_rclone_path,
    is_rclone_config,
    list_remotes,
)
from bot.helper.telegram_helper.message_utils import editMarkup, sendMessage
from bot.helper.telegram_helper.button_build import ButtonMaker


async def handle_storage(client, message):
    if await is_rclone_config(message.from_user.id, message):
        await list_remotes(message, menu_type=Menus.STORAGE)


async def storage_menu_cb(client, callback_query):
    query = callback_query
    data = query.data
    cmd = data.split("^")
    message = query.message
    user_id = query.from_user.id

    if int(cmd[-1]) != user_id:
        await query.answer("⛔ This menu is not for you!", show_alert=True)
        return
    if cmd[1] == "remote":
        await rclone_about(message, query, cmd[2], user_id)
    elif cmd[1] == "back":
        await list_remotes(message, menu_type=Menus.STORAGE, edit=True)
        await query.answer()
    elif cmd[1] == "close":
        await query.answer()
        await message.delete()


async def rclone_about(message, query, remote_name, user_id):
    button = ButtonMaker()
    conf_path = await get_rclone_path(user_id, message)
    cmd = ["rclone", "about", "--json", f"--config={conf_path}", f"{remote_name}:"]
    process = await exec(*cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = await process.communicate()
    return_code = await process.wait()
    stdout = stdout.decode().strip()
    if return_code != 0:
        err = html_escape(stderr.decode().strip())
        await sendMessage(f"<b>Error:</b> <code>{err}</code>", message)
        return
    info = loads(stdout)
    if len(info) == 0:
        await query.answer("💾 Team Drive with Unlimited Storage", show_alert=True)
        return
    result_msg = "💾 <b>Storage Details</b>\n"
    try:
        used = get_readable_file_size(info["used"])
        total = get_readable_file_size(info["total"])
        free = get_readable_file_size(info["free"])
        used_percentage = 100 * float(info["used"]) / float(info["total"])
        used_bar = get_used_bar(used_percentage)
        used_percentage = f"{round(used_percentage, 2)}%"
        free_percentage = round((info["free"] * 100) / info["total"], 2)
        free_percentage = f"{free_percentage}%"
        result_msg += f"\n<code>{used_bar}</code>"
        result_msg += f"\n<b>Used:</b> <code>{used}</code> of <code>{total}</code>"
        result_msg += f"\n<b>Free:</b> <code>{free}</code> of <code>{total}</code>"
        result_msg += f"\n<b>Trashed:</b> <code>{get_readable_file_size(info['trashed'])}</code>"
        result_msg += f"\n\n<b>Storage Used:</b> <code>{used_percentage}</code>"
        result_msg += f"\n<b>Storage Free:</b> <code>{free_percentage}</code>"
    except KeyError:
        result_msg += "\n<b>N/A</b>"
    button.cb_buildbutton("⬅️ Back", f"storagemenu^back^{user_id}", "footer")
    button.cb_buildbutton(
        "✘ Close Menu", f"storagemenu^close^{user_id}", "footer_second"
    )
    await editMarkup(result_msg, message, reply_markup=button.build_menu(1))


def get_used_bar(percentage):
    return "{0}{1}".format(
        "".join(["■" for i in range(floor(percentage / 10))]),
        "".join(["□" for i in range(10 - floor(percentage / 10))]),
    )


bot.add_handler(
    MessageHandler(
        handle_storage,
        filters=command(BotCommands.StorageCommand)
        & (CustomFilters.user_filter | CustomFilters.chat_filter),
    )
)
bot.add_handler(CallbackQueryHandler(storage_menu_cb, filters=regex("storagemenu")))
