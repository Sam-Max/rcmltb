from bot import Bot
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.filters import CustomFilters
from pyrogram.handlers import MessageHandler
from pyrogram.filters import command
from bot.helper.ext_utils.human_format import human_readable_bytes
from bot.helper.ext_utils.message_utils import sendMessage
from speedtest import Speedtest

async def speed_handler(client, message):
    edit_msg = await sendMessage("Running speedtest", message)    
    test = Speedtest()
    test.get_best_server()
    test.download()
    test.upload()
    test.results.share()
    result = test.results.dict()
    string_speed = "<b>Speedtest Result:</b>\n"
    string_speed += f'\n<b>Server Name:</b> {result["server"]["name"]}'
    string_speed += f'\n<b>Country:</b> {result["server"]["country"]} {result["server"]["cc"]}'
    string_speed += f'\n<b>Sponsor:</b> {result["server"]["sponsor"]}'
    string_speed += f'\n<b>Upload:</b> {human_readable_bytes(result["upload"] / 8)}/s'
    string_speed += f'\n<b>Download:</b>{human_readable_bytes(result["download"] / 8)}/s'
    string_speed += f'\n<b>Ping:</b> {result["ping"]} ms'
    string_speed += f'\n<b>ISP:</b> {result["client"]["isp"]}'
    await edit_msg.delete()
    await sendMessage(string_speed, message)

start = MessageHandler(speed_handler, filters= command(BotCommands.SpeedtestCommand) & CustomFilters.owner_filter)
Bot.add_handler(start)
