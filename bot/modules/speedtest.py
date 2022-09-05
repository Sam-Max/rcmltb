from bot import ALLOWED_CHATS, ALLOWED_USERS, OWNER_ID, bot
from telethon.events import NewMessage
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.bot_utils import command_process
from bot.helper.ext_utils.speedtest import get_speed

async def speed_handler(e):
    user_id= e.sender_id
    chat_id= e.chat_id
    if user_id in ALLOWED_USERS or chat_id in ALLOWED_CHATS or user_id == OWNER_ID:
        await get_speed(e)
    else:
        await e.reply('Not Authorized user')

bot.add_event_handler(speed_handler, NewMessage(pattern=command_process(f"/{BotCommands.SpeedtestCommand}")))