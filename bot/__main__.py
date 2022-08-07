import logging
from bot.core.handlermanager import add_handlers
from bot.utils.bot_utils.misc_utils import start_cleanup
from . import bot

logging.basicConfig(level=logging.INFO,
        format="%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s")

start_cleanup()
print("Successfully deployed!")

if __name__ == "__main__":
    
    add_handlers(bot)

    try:
        bot.loop.run_until_complete()
    except:
        pass

    bot.run_until_disconnected()

