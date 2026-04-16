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
            await sendMessage(f"GID: <code>{gid}</code> Not Found.", message)
            return
    elif reply_to_id := message.reply_to_message_id:
        async with status_dict_lock:
            task = status_dict.get(reply_to_id)
        if task is None:
            await sendMessage("This is not an active task!", message)
            return
    elif len(msg) in {1, 2}:
        cmds = BotCommands.ForceStartCommand
        help_msg = f"""Reply to an active Command message which was used to start the download/upload.
<code>/{cmds[0]}</code> fd (to remove it from download queue) or fu (to remove it from upload queue) or nothing to remove it from both queues.
Also send <code>/{cmds[0]} GID</code> fu|fd or only gid to force start by removing the task from queue!
Examples:
<code>/{cmds[1]}</code> GID fu (force upload)
<code>/{cmds[1]}</code> GID (force download and upload)
By reply to task cmd:
<code>/{cmds[1]}</code> (force download and upload)
<code>/{cmds[1]}</code> fd (force download)"""
        await sendMessage(help_msg, message)
        return
    if (
        Config.OWNER_ID != user_id
        and task.listener.user_id != user_id
        and (user_id not in user_data or not user_data[user_id].get("is_sudo"))
    ):
        await sendMessage("This task is not for you!", message)
        return
    listener = task.listener
    result_msg = ""
    async with queue_dict_lock:
        if status == "fu":
            listener.force_upload = True
            if listener.uid in queued_up:
                await start_up_from_queued(listener.uid)
                result_msg = "Task has been force started to upload!"
            else:
                result_msg = "Force upload enabled for this task!"
        elif status == "fd":
            listener.force_download = True
            if listener.uid in queued_dl:
                await start_dl_from_queued(listener.uid)
                result_msg = "Task has been force started to download only!"
            else:
                result_msg = "This task is not in download queue!"
        else:
            listener.force_download = True
            listener.force_upload = True
            if listener.uid in queued_up:
                await start_up_from_queued(listener.uid)
                result_msg = "Task has been force started to upload!"
            elif listener.uid in queued_dl:
                await start_dl_from_queued(listener.uid)
                result_msg = "Task has been force started to download and upload will start once download finishes!"
            else:
                result_msg = "This task is not in queue!"
    if result_msg:
        await sendMessage(result_msg, message)
