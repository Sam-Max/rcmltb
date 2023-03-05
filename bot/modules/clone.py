# Source: https://github.com/anasty17/mirror-leech-telegram-bot/blob/master/bot/modules/clone.py
# Adapted for asyncio framework and pyrogram library

from random import SystemRandom
from string import ascii_letters, digits
from bot import bot, LOGGER, status_dict, status_dict_lock, Interval, config_dict
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.bot_utils import is_gdrive_link, run_sync
from bot.helper.ext_utils.filters import CustomFilters
from bot.helper.ext_utils.message_utils import delete_all_messages, deleteMessage, sendMarkup, sendMessage, sendStatusMessage, update_all_messages
from bot.helper.mirror_leech_utils.status_utils.clone_status import CloneStatus
from bot.helper.mirror_leech_utils.upload_utils.gdriveTools import GoogleDriveHelper
from pyrogram import filters
from pyrogram.handlers import MessageHandler



async def _clone(client, message):
    if not config_dict['GDRIVE_FOLDER_ID']:
        await sendMessage(message, 'GDRIVE_FOLDER_ID not Provided!')
        return
    args = message.text.split()
    reply_to = message.reply_to_message
    link = ''
    tag = ''
    if len(args) > 1:
        link = args[1].strip()
        if message.from_user.username:
            tag = f"@{message.from_user.username}"
    if reply_to:
        if len(link) == 0:
            link = reply_to.text.split(maxsplit=1)[0].strip()
        if reply_to.from_user.username:
            tag = f"@{reply_to.from_user.username}"
    if is_gdrive_link(link):
        gd = GoogleDriveHelper()
        res, size, name, files = await run_sync(gd.helper, link)
        if res != "":
            return await sendMessage(res, message)
        if files <= 20:
            msg= await sendMessage(f"Cloning: <code>{link}</code>", message)
            result, button = await run_sync(gd.clone, link) 
            await deleteMessage(msg)
        else:
            gd = GoogleDriveHelper(name)
            gid = ''.join(SystemRandom().choices(ascii_letters + digits, k=12))
            async with status_dict_lock:
                status_dict[message.id] = CloneStatus(gd, size, message, gid)
            await sendStatusMessage(message)
            result, button = await run_sync(gd.clone, link) 
            async with status_dict_lock:
                del status_dict[message.id]
                count = len(status_dict)
            try:
                if count == 0:
                    if Interval:
                        Interval[0].cancel()
                        del Interval[0]
                    await delete_all_messages()
                else:
                    await update_all_messages()
            except IndexError:
                pass
        cc = f'\n\n<b>cc: </b>{tag}'
        if button in ["cancelled", ""]:
            await sendMessage(f"{tag} {result}", message)
        else:
            await sendMarkup(result + cc, message, button)
            LOGGER.info(f'Cloning Done: {name}')
    else:
        await sendMessage("Send gdrive link along with command or reply to the link with command", message)


clone_handler = MessageHandler(_clone, filters= filters.command(BotCommands.CloneCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter))
bot.add_handler(clone_handler)
