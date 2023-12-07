from asyncio import sleep, QueueEmpty
from pyrogram.filters import regex
from bot import (
    status_dict_lock,
    OWNER_ID,
    bot,
    status_dict,
    user_data,
    m_queue,
    l_queue,
)
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from pyrogram.handlers import CallbackQueryHandler, MessageHandler
from pyrogram import filters
from bot.helper.telegram_helper.message_utils import sendMarkup, sendMessage
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.misc_utils import getAllDownload, getDownloadByGid
from bot.helper.mirror_leech_utils.status_utils.status_utils import MirrorStatus


async def cancel_mirror(client, message):
    user_id = message.from_user.id
    msg = message.text.split()
    if len(msg) > 1:
        gid = msg[1]
        dl = await getDownloadByGid(gid)
        if not dl:
            await sendMessage(f"GID: <code>{gid}</code> Not Found.", message)
            return
    elif reply_to_id := message.reply_to_message_id:
        async with status_dict_lock:
            dl = status_dict.get(reply_to_id, None)
        if dl is None:
            await sendMessage(message, "This is not an active task!")
            return
    elif len(msg) == 1:
        msg = (
            "Reply to an active Command message which was used to start the download"
            f" or send <code>/{BotCommands.CancelCommand} GID</code> to cancel it!"
        )
        await sendMessage(message, msg)
        return

    if (
        OWNER_ID != user_id
        and dl.message.from_user.id != user_id
        and (user_id not in user_data or not user_data[user_id].get("is_sudo"))
    ):
        await sendMessage("This is not for you!", message)
        return

    if dl.type() == "RcloneSync":
        dl.download().kill
    else:
        await dl.download().cancel_download()


async def cancell_all_buttons(client, message):
    async with status_dict_lock:
        count = len(status_dict)
    if count == 0:
        await sendMessage("No active tasks", message)
        return
    buttons = ButtonMaker()
    buttons.cb_buildbutton("Downloading", f"canall {MirrorStatus.STATUS_DOWNLOADING}")
    buttons.cb_buildbutton("Uploading", f"canall {MirrorStatus.STATUS_UPLOADING}")
    buttons.cb_buildbutton("Seeding", f"canall {MirrorStatus.STATUS_SEEDING}")
    buttons.cb_buildbutton("Cloning", f"canall {MirrorStatus.STATUS_CLONING}")
    buttons.cb_buildbutton("Paused", f"canall {MirrorStatus.STATUS_PAUSED}")
    buttons.cb_buildbutton("Mirror Queue", f"canall mqueue")
    buttons.cb_buildbutton("Leech Queue", f"canall lqueue")
    buttons.cb_buildbutton("All", "canall all")
    buttons.cb_buildbutton("Close", "canall close")
    await sendMarkup("Choose tasks to cancel.", message, buttons.build_menu(2))


async def cancel_all_update(client, query):
    message = query.message
    tag = f"@{message.from_user.username}"
    data = query.data.split()
    await query.answer()
    if data[1] == "mqueue":
        try:
            while True:
                m_queue.get_nowait()
                m_queue.task_done()
        except QueueEmpty:
            await sendMessage(f"{tag} your mirror queue has been cancelled", message)
        return
    elif data[1] == "lqueue":
        try:
            while True:
                l_queue.get_nowait()
                l_queue.task_done()
        except QueueEmpty:
            await sendMessage(f"{tag} your mirror queue has been cancelled", message)
        return
    elif data[1] == "close":
        await query.message.delete()
    else:
        res = await cancel_all_(data[1])
        if not res:
            await sendMessage(f"No matching tasks for {data[1]}!", message)


async def cancel_all_(status):
    matches = await getAllDownload(status)
    if not matches:
        return False
    for dl in matches:
        obj = dl.download()
        await obj.cancel_download()
        await sleep(1)
    return True


cancel_mirror_handler = MessageHandler(
    cancel_mirror,
    filters.command(BotCommands.CancelCommand)
    & (CustomFilters.user_filter | CustomFilters.chat_filter),
)
cancel_all_handler = MessageHandler(
    cancell_all_buttons,
    filters=filters.command(BotCommands.CancelAllCommand)
    & (CustomFilters.owner_filter | CustomFilters.sudo_filter),
)
cancel_all_cb = CallbackQueryHandler(
    cancel_all_update,
    filters=regex("canall") & (CustomFilters.owner_filter | CustomFilters.sudo_filter),
)

bot.add_handler(cancel_mirror_handler)
bot.add_handler(cancel_all_handler)
bot.add_handler(cancel_all_cb)
