from pyrogram.handlers import CallbackQueryHandler
from pyrogram import filters
from asyncio import iscoroutinefunction
from aiofiles.os import remove, path as aiopath
from bot import bot, status_dict, status_dict_lock, user_data, LOGGER
from bot.core.torrent_manager import TorrentManager
from bot.core.config_manager import Config
from bot.helper.telegram_helper.message_utils import sendMessage, sendStatusMessage, deleteMessage
from bot.helper.ext_utils.misc_utils import getTaskByGid, bt_selection_buttons
from bot.helper.ext_utils.bot_utils import new_task
from bot.helper.mirror_leech_utils.status_utils.status_utils import MirrorStatus


@new_task
async def select(_, message):
    """Handle /sel command to select files from an active torrent download."""
    user_id = message.from_user.id if message.from_user else message.sender_chat.id
    msg = message.text.split()
    if len(msg) > 1:
        gid = msg[1]
        task = await getTaskByGid(gid)
        if task is None:
            await sendMessage(f"🔍 <b>Task Not Found</b>\n\nGID: <code>{gid}</code>", message)
            return
    elif reply_to_id := message.reply_to_message_id:
        async with status_dict_lock:
            task = status_dict.get(reply_to_id)
        if task is None:
            await sendMessage("📭 <b>No Active Task</b>\n\nThis message is not associated with an active task.", message)
            return
    elif len(msg) == 1:
        help_msg = (
            "📂 <b>File Selector</b>\n\n"
            "Select specific files from an active torrent download.\n\n"
            "<b>Usage:</b>\n"
            "<code>/sel GID</code> — select by GID\n"
            "Reply to task message with <code>/sel</code>\n\n"
            "You can also use the <code>s</code> argument when starting a download to select files before downloading begins."
        )
        await sendMessage(help_msg, message)
        return
    if (
        Config.OWNER_ID != user_id
        and task.listener.user_id != user_id
        and (user_id not in user_data or not user_data[user_id].get("is_sudo"))
    ):
        await sendMessage("🚫 <b>Access Denied</b>\n\nThis task does not belong to you.", message)
        return
    if not iscoroutinefunction(task.status):
        await sendMessage("ℹ️ <b>Already Downloaded</b>\n\nThe download stage has already finished.", message)
        return
    current_status = await task.status()
    if current_status not in [
        MirrorStatus.STATUS_DOWNLOADING,
        MirrorStatus.STATUS_PAUSED,
        MirrorStatus.STATUS_QUEUEDL,
    ]:
        await sendMessage(
            "⚠️ <b>Cannot Select</b>\n\nTask must be in downloading, paused, or queued status.",
            message,
        )
        return
    if task.name().startswith("[METADATA]") or task.name().startswith("Trying"):
        await sendMessage("⏳ <b>Still Loading</b>\n\nPlease wait for metadata download to finish.", message)
        return

    try:
        if not task.queued:
            await task.update()
            id_ = task.gid()
            if hasattr(task, "seeding"):
                if task.listener.is_qbit:
                    id_ = await task.hash()
                    await TorrentManager.qbittorrent.torrents.stop([id_])
                else:
                    try:
                        await TorrentManager.aria2.forcePause(id_)
                    except Exception as e:
                        LOGGER.error(
                            f"{e} Error in pause, this mostly happens after abuse aria2"
                        )
        task.listener.select = True
    except Exception:
        await sendMessage("❌ <b>Error</b>\n\nThis is not a bittorrent task.", message)
        return

    SBUTTONS = bt_selection_buttons(id_)
    msg = "📂 <b>File Selection</b>\n\nDownload paused. Choose files then press <b>Done Selecting</b> to resume."
    await sendMessage(msg, message, SBUTTONS)


async def get_confirm(client, query):
    """Handle btsel callbacks for file selection confirmation."""
    user_id = query.from_user.id
    data = query.data.split()
    message = query.message
    task = await getTaskByGid(data[2])
    if task is None:
        await query.answer("❌ This task has been cancelled!", show_alert=True)
        await deleteMessage(message)
        return
    if not hasattr(task, "seeding"):
        await query.answer(
            "ℹ️ Download stage already finished. Keep this message to resume seeding if enabled.",
            show_alert=True,
        )
        return
    if hasattr(task, "listener"):
        listener = task.listener()
    else:
        return
    if user_id != listener.user_id:
        await query.answer("⛔ This task does not belong to you!", show_alert=True)
    elif data[1] == "pin":
        await query.answer(data[3], show_alert=True)
    elif data[1] == "done":
        await query.answer()
        id_ = data[3]
        if len(id_) > 20:
            tor_info = await TorrentManager.qbittorrent.torrents.info(hash=id_)
            if tor_info:
                tor_info = tor_info[0]
                path = tor_info.content_path.rsplit("/", 1)[0]
                res = await TorrentManager.qbittorrent.torrents.files(hash=id_)
                for f in res:
                    if f.priority == 0:
                        f_paths = [f"{path}/{f.name}", f"{path}/{f.name}.!qB"]
                        for f_path in f_paths:
                            if await aiopath.exists(f_path):
                                try:
                                    await remove(f_path)
                                except Exception:
                                    pass
                await TorrentManager.qbittorrent.torrents.resume(hashes=[id_])
        else:
            try:
                download = await TorrentManager.aria2.tellStatus(id_)
                files = download.get("files", [])
                for f in files:
                    if not f.get("selected", True):
                        f_path = f.get("path", "")
                        if await aiopath.exists(f_path):
                            try:
                                await remove(f_path)
                            except Exception:
                                pass
                await TorrentManager.aria2.unpause(id_)
            except Exception as e:
                LOGGER.error(
                    f"{e} Error in resume, this mostly happens after abuse aria2. Try to use select cmd again!"
                )
        await sendStatusMessage(message)
        await deleteMessage(message)
    elif data[1] == "rm":
        await query.answer()
        obj = task.task()
        await obj.cancel_task()
        await deleteMessage(message)


bot.add_handler(CallbackQueryHandler(get_confirm, filters=filters.regex("btsel")))
