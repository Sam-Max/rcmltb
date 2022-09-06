from bot import Bot
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.filters import CustomFilters
from bot.helper.ext_utils.speedtest import get_speed
from pyrogram.handlers import MessageHandler
from pyrogram.filters import command

async def speed_handler(client, message):
    await get_speed(client, message)

start = MessageHandler(speed_handler, filters= command(BotCommands.SpeedtestCommand) & CustomFilters.owner_filter)
Bot.add_handler(start)
