from time import time
from psutil import cpu_percent, virtual_memory, disk_usage
from bot import (
    DOWNLOAD_DIR,
    bot,
    Interval,
    status_dict,
    status_dict_lock,
    status_reply_dict_lock,
    config_dict,
    botUptime,
)
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram import filters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.ext_utils.bot_utils import get_readable_time, setInterval, turn
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.ext_utils.human_format import get_readable_file_size
from bot.helper.telegram_helper.message_utils import (
    auto_delete_message,
    sendMessage,
    sendStatusMessage,
    update_all_messages,
)


async def status_handler(client, message):
    async with status_dict_lock:
        count = len(status_dict)
    if count == 0:
        currentTime = get_readable_time(time() - botUptime)
        free = get_readable_file_size(disk_usage(DOWNLOAD_DIR).free)
        msg = "No Active Downloads !\n___________________________"
        msg += (
            f"\n<b>CPU:</b> {cpu_percent()}% | <b>FREE:</b> {free}"
            f"\n<b>RAM:</b> {virtual_memory().percent}% | <b>UPTIME:</b> {currentTime}"
        )
        reply_message = await sendMessage(msg, message)
        await auto_delete_message(message, reply_message)
    else:
        await sendStatusMessage(message)
        async with status_reply_dict_lock:
            try:
                if Interval:
                    Interval[0].cancel()
                    Interval.clear()
            except:
                pass
            finally:
                Interval.append(
                    setInterval(
                        config_dict["STATUS_UPDATE_INTERVAL"], update_all_messages
                    )
                )


async def status_pages(client, callback_query):
    query = callback_query
    await query.answer()
    data = query.data.split()
    if data[1] == "ref":
        await update_all_messages(True)
    else:
        await turn(data)


status_handlers = MessageHandler(
    status_handler,
    filters=filters.command(BotCommands.StatusCommand)
    & (CustomFilters.user_filter | CustomFilters.chat_filter),
)
status_pages_handler = CallbackQueryHandler(
    status_pages, filters=filters.regex("status")
)

bot.add_handler(status_handlers)
bot.add_handler(status_pages_handler)
