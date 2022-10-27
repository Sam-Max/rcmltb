
import asyncio
from time import sleep
from pyrogram.filters import regex
from bot import status_dict_lock, OWNER_ID, SUDO_USERS, bot, status_dict, botloop
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.filters import CustomFilters
from pyrogram.handlers import CallbackQueryHandler, MessageHandler
from pyrogram import filters
from bot.helper.ext_utils.message_utils import sendMarkup, sendMessage
from bot.helper.ext_utils.misc_utils import ButtonMaker, getAllDownload, getDownloadByGid
from bot.helper.mirror_leech_utils.status_utils.status_utils import MirrorStatus


async def cancel_mirror(client, message):
    user_id = message.from_user.id
    args= message.text.split()
    if len(args) > 1:
        gid = args[1]
        dl = getDownloadByGid(gid)
        if not dl:
           return await sendMessage(f"GID: <code>{gid}</code> Not Found.", message)
    else:
        msg = f"send <code>/{BotCommands.CancelCommand} GID</code> to cancel task"
        return await sendMessage(msg, message)

    if OWNER_ID != user_id and user_id not in SUDO_USERS:
        return await sendMessage("This is not for you!", message)

    dl.download().cancel_download()

async def cancell_all_buttons(client, message):
    async with status_dict_lock:
        count = len(status_dict)
    if count == 0:
        return await sendMessage("No active tasks", message)
    buttons = ButtonMaker()
    buttons.cb_buildbutton("Downloading", f"canall {MirrorStatus.STATUS_DOWNLOADING}")
    buttons.cb_buildbutton("Uploading", f"canall {MirrorStatus.STATUS_UPLOADING}")
    buttons.cb_buildbutton("All", "canall all")
    buttons.cb_buildbutton("Close", "canall close")
    await sendMarkup('Choose tasks to cancel.', message, buttons.build_menu(2))

async def cancel_all_update(client, callbackquery):
    query = callbackquery
    user_id = query.from_user.id
    data = query.data
    data = data.split()
    if CustomFilters._owner_query(user_id):
        await query.answer()
        if data[1] == 'close':
            return await query.message.delete()
        botloop.run_in_executor(None, cancel_all_, data[1], botloop)
    else:
        await query.answer(text="You don't have permission to use these buttons", show_alert=True)

def cancel_all_(status, loop):
    gid = ''
    while dl := asyncio.run_coroutine_threadsafe(getAllDownload(status), loop).result():
        if dl.gid() != gid:
            gid = dl.gid()
            dl.download().cancel_download()
            sleep(1)

cancel_mirror_handler = MessageHandler(cancel_mirror, filters.command(BotCommands.CancelCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter))
cancel_all_handler = MessageHandler(cancell_all_buttons, filters= filters.command(BotCommands.CancelAllCommand) & (CustomFilters.owner_filter | CustomFilters.sudo_filter))
cancel_all_cb = CallbackQueryHandler(cancel_all_update, filters= regex("canall"))

bot.add_handler(cancel_mirror_handler)  
bot.add_handler(cancel_all_handler)
bot.add_handler(cancel_all_cb)

        
 