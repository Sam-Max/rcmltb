from bot.core.handlermanager import add_handlers
from bot.utils.bot_utils.misc_utils import start_cleanup
from . import bot, Bot
from os import path as ospath, remove as osremove
from bot import OWNER_ID

print("Successfully deployed!")

async def main():
    start_cleanup()
    if ospath.isfile(".restartmsg"):
        with open(".restartmsg") as f:
            cht_id, msg_id = map(int, f)
        await Bot.edit_message_text(text= "Restarted successfully!", message_id= msg_id,
                                chat_id= cht_id)     
        osremove(".restartmsg")
    await Bot.send_message(OWNER_ID, text="The bot is ready to use")
    add_handlers(bot)

bot.loop.run_until_complete(main())

try:
    bot.loop.run_until_complete()
except:
    pass

bot.run_until_disconnected()

