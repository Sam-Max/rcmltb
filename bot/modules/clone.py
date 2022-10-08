#Source: https://github.com/anasty17/mirror-leech-telegram-bot/blob/master/bot/modules/clone.py
# Adapted for asyncio framework and pyrogram library

import asyncio
from random import SystemRandom
from string import ascii_letters, digits
from bot import Bot, LOGGER, status_dict, status_dict_lock, Interval
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.bot_utils import is_gdrive_link
from bot.helper.ext_utils.filters import CustomFilters
from bot.helper.ext_utils.message_utils import editMarkup, editMessage, sendMessage
from bot.helper.mirror_leech_utils.status_utils.clone_status import CloneStatus
from bot.helper.mirror_leech_utils.upload_utils.gdriveTools import GoogleDriveHelper
from pyrogram import filters
from pyrogram.handlers import MessageHandler

async def _clone(client, message):
    args = message.text.split()
    reply_to = message.reply_to_message
    link = ''
    if len(args) > 1:
        link = args[1].strip()
        if message.from_user.username:
            tag = f"@{message.from_user.username}"
        else:
            tag = message.from_user.mention_html(message.from_user.first_name)
    if reply_to:
        if len(link) == 0:
            link = reply_to.text.split(maxsplit=1)[0].strip()
        if reply_to.from_user.username:
            tag = f"@{reply_to.from_user.username}"
        else:
            tag = reply_to.from_user.mention_html(reply_to.from_user.first_name)
    if is_gdrive_link(link):
        loop= asyncio.get_running_loop()
        gd = GoogleDriveHelper()
        res, size, name, files = await loop.run_in_executor(None, gd.helper, link)
        if res != "":
            return await sendMessage(res, message)
        if files <= 20:
            msg = await sendMessage(f"Cloning: <code>{link}</code>", message)
            result, button = await loop.run_in_executor(None, gd.clone, link) 
        else:
            gd = GoogleDriveHelper(name)
            gid = ''.join(SystemRandom().choices(ascii_letters + digits, k=12))
            clone_status = CloneStatus(gd, size, message, gid)
            async with status_dict_lock:
                status_dict[message.id] = clone_status
            status_task= loop.create_task(clone_status.start())
            result, button = await loop.run_in_executor(None, gd.clone, link) 
            await status_task
            msg = status_task.result()
            async with status_dict_lock:
                del status_dict[message.id]
            count = len(status_dict)
            try:
                if count == 0:
                    Interval[0].cancel()
                    del Interval[0]
            except IndexError:
                pass
        cc = f'\n\n<b>cc: </b>{tag}'
        if button in ["cancelled", ""]:
            await editMessage(f"{tag} {result}", msg)
        else:
            await editMarkup(result + cc, msg, button)
            LOGGER.info(f'Cloning Done: {name}')
    else:
        await sendMessage("Send gdrive link along with command or reply to the link with command", message)



clone_handler = MessageHandler(_clone, filters= filters.command(BotCommands.CloneCommand) & (CustomFilters.user_filter | CustomFilters.chat_filter))
Bot.add_handler(clone_handler)
