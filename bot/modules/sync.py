from random import SystemRandom
from string import ascii_letters, digits
from pyrogram.filters import command, regex
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from asyncio.subprocess import PIPE, create_subprocess_exec as exec
from bot import bot, config_dict, status_dict_lock, status_dict
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.ext_utils.rclone_utils import get_rclone_path, is_rclone_config, list_remotes
from bot.helper.telegram_helper.message_utils import sendStatusMessage
from bot.modules.tasks_listener import MirrorLeechListener
from bot.helper.mirror_leech_utils.status_utils.sync_status import SyncStatus


SOURCE= None
listener_dict= {}



async def handle_sync(client, message):
    user_id= message.from_user.id
    tag = f"@{message.from_user.username}"
    if await is_rclone_config(user_id, message):
        await list_remotes(message, menu_type="syncmenu", remote_type='source')
        listener= MirrorLeechListener(message, tag, user_id)
        listener_dict[message.id] = listener

async def sync_cb(client, callbackQuery):
    query= callbackQuery
    data= query.data
    data = data.split("^")
    message= query.message
    user_id= query.from_user.id
    msg_id= query.message.reply_to_message.id
    listener= listener_dict[msg_id] 
    path = await get_rclone_path(user_id, message)

    if data[1] == "source":
        await query.answer()
        globals()['SOURCE']= data[2]
        await list_remotes(message, menu_type="syncmenu", remote_type='destination', edit=True)
    elif data[1] == "destination":  
        await query.answer()
        destination = data[2]
        await start_sync(message, path, destination, listener)
    else:
        await query.answer()
        await message.delete()

async def start_sync(message, path, destination, listener):
    if config_dict["SERVER_SIDE"]:
        cmd = ["rclone", "sync", "--server-side-across-configs", "--delete-during", "-P", f'--config={path}', f"{SOURCE}:", f"{destination}:"] 
    else:
        cmd = ["rclone", "sync", "--delete-during", "-P", f'--config={path}', f"{SOURCE}:", f"{destination}:"] 
    process = await exec(*cmd, stdout=PIPE, stderr=PIPE)
    gid = ''.join(SystemRandom().choices(ascii_letters + digits, k=10))
    async with status_dict_lock:
        status = SyncStatus(process, gid, SOURCE, destination)
        status_dict[listener.uid] = status
    await sendStatusMessage(listener.message)
    await status.read_stdout()
    return_code = await process.wait()
    if return_code != 0:
        err= await process.stderr.read()
        await listener.onDownloadError(str(err))
    else:
        msg= 'Sync completed successfully✅'
        msg+= '<b>\n\nNote:</b>' 
        msg+= '\n1.Use dedupe command to remove duplicate file/directory'
        msg+= '\n2.Use rmdir command to remove empty directories'
        await listener.onRcloneSyncComplete(msg)
    await message.delete()



sync = MessageHandler(handle_sync, filters=command(BotCommands.SyncCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter))
sync_callback= CallbackQueryHandler(sync_cb, filters= regex("syncmenu"))

bot.add_handler(sync)
bot.add_handler(sync_callback)
