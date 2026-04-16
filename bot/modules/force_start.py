from bot import (
    status_dict,
    status_dict_lock,
    user_data,
    queued_up,
    queued_dl,
    queue_dict_lock,
    LOGGER,
)
from bot.core.config_manager import Config
from bot.helper.ext_utils.bot_utils import new_task
from bot.helper.ext_utils.misc_utils import getTaskByGid
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.message_utils import sendMessage
from bot.helper.ext_utils.task_manager import start_dl_from_queued, start_up_from_queued


@new_task
async def remove_from_queue(_, message):
    user_id = message.from_user.id if message.from_user else message.sender_chat.id
    msg = message.text.split()
    status = msg[1] if len(msg) > 1 and msg[1] in ["fd", "fu"] else ""
    if status and len(msg) > 2 or not status and len(msg) > 1:
        gid = msg[2] if status else msg[1]
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
    elif len(msg) in {1, 2}:
        cmds = BotCommands.ForceStartCommand
        help_msg = (
            "⚡ <b>Force Start</b>\n\n"
            "Bypass queue limits and start a task immediately.\n\n"
            "<b>Usage:</b>\n"
            f"<code>/{cmds[0]}</code> — force download + upload (reply to task)\n"
            f"<code>/{cmds[0]} fd</code> — force download only (reply to task)\n"
            f"<code>/{cmds[0]} fu</code> — force upload only (reply to task)\n"
            f"<code>/{cmds[0]} GID</code> — force by GID\n"
            f"<code>/{cmds[1]} GID fu</code> — force upload by GID\n\n"
            "<b>Flags:</b>\n"
            "• <code>fd</code> — force download\n"
            "• <code>fu</code> — force upload"
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
    listener = task.listener
    result_msg = ""
    async with queue_dict_lock:
        if status == "fu":
            listener.force_upload = True
            if listener.uid in queued_up:
                await start_up_from_queued(listener.uid)
                result_msg = "<b>Force Start</b>\n\nTask bypassed upload queue and started uploading."
            else:
                result_msg = "⚡ <b>Force Start</b>\n\nForce upload enabled for this task."
        elif status == "fd":
            listener.force_download = True
            if listener.uid in queued_dl:
                await start_dl_from_queued(listener.uid)
                result_msg = "⚡ <b>Force Start</b>\n\nTask bypassed download queue and started downloading."
            else:
                result_msg = "ℹ️ <b>Force Start</b>\n\nThis task is not in the download queue."
        else:
            listener.force_download = True
            listener.force_upload = True
            if listener.uid in queued_up:
                await start_up_from_queued(listener.uid)
                result_msg = "⚡ <b>Force Start</b>\n\nTask bypassed upload queue and started uploading."
            elif listener.uid in queued_dl:
                await start_dl_from_queued(listener.uid)
                result_msg = "⚡ <b>Force Start</b>\n\nTask bypassed download queue. Upload will start once download finishes."
            else:
                result_msg = "ℹ️ <b>Force Start</b>\n\nThis task is not in any queue."
    if result_msg:
        await sendMessage(result_msg, message)
